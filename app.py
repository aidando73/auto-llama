import os
from llama_stack_client import LlamaStackClient
from tools import SANDBOX_DIR, TOOLS, run_tool
import json

# Works:
# MODEL_ID = "meta-llama/Llama-3.1-405B-Instruct-FP8"
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"

# Doesn't work currently:
# MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
# MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"


# Number of code review cycles
CODE_REVIEW_CYCLES = 5

# No limit on output tokens
MAX_TOKENS = 200_000


PROGRAM_OBJECTIVE="a web server that has an API endpoint that translates text from English to French."

CODER_AGENT_SYSTEM_PROMPT=f"""
You are a software engineer who is writing code to build a python codebase: {PROGRAM_OBJECTIVE}.
"""

REVIEWER_AGENT_SYSTEM_PROMPT=f"""
You are a senior software engineer who is reviewing the codebase that was created by another software engineer.
The program is {PROGRAM_OBJECTIVE}.
If you think the codebase is good enough to ship, please say LGTM.
"""


def get_codebase_contents():
    contents = ""
    for root, dirs, files in os.walk(SANDBOX_DIR):
        for file in files:
            # concatenate the file name
            contents += f"file: {file}:\n"
            with open(os.path.join(root, file), "r") as f:
                contents += f.read()
            contents += "\n\n"
    return contents


BLUE = "\033[94m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
RESET = "\033[0m"


client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

review_feedback = None
for i in range(1, CODE_REVIEW_CYCLES + 1):
    print(f"{BLUE}Coder Agent - Creating Plan - Iteration {i}{RESET}")
    if review_feedback:
        prompt_feedback = f"""
        One of your peers has provided the following feedback:
        {review_feedback}
        Please adjust the plan to address the feedback.

        
        """
    else:
        prompt_feedback = ""

    prompt =f"""
        Create a step by step plan to complete the task of creating a codebase that will {PROGRAM_OBJECTIVE}.
        You have 3 different operations you can perform. You can create a file, update a file, or delete a file.
        Limit your step by step plan to only these operations per step.

        Here is the codebase currently:
        {get_codebase_contents()}

        {prompt_feedback}
        Please ensure there's a README.md file in the root of the codebase that describes the codebase and how to run it.
        Please ensure there's a requirements.txt file in the root of the codebase that describes the dependencies of the codebase.
        """
    response = client.inference.chat_completion(
        model_id=MODEL_ID,
        messages=[
            {"role": "system", "content": CODER_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        sampling_params={
            "max_tokens": MAX_TOKENS,
        },
        response_format={
            "type": "json_schema",
            "json_schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Plan",
                "description": f"A plan to complete the task of creating a codebase that will {PROGRAM_OBJECTIVE}.",
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["steps"],
                "additionalProperties": False
            }
        },
    )
    try:
        plan = json.loads(response.completion_message.content)
    except Exception as e:
        print(f"Error parsing plan: {e}")
        plan = {"steps": []}
    for step_idx, step in enumerate(plan["steps"]):
        print(f"{step_idx + 1}. {step}")
    print("\n")

    # Coding agent executes the plan
    print(f"{BLUE}Coder Agent - Executing Plan - Iteration {i}{RESET}")
    if review_feedback:
        prompt_feedback = f"""
        Keep in mind one a senior engineer has provided the following feedback:
        {review_feedback}

        """
    else:
        prompt_feedback = ""

    for step in plan["steps"]:
        prompt = f"""
            You have 3 different operations you can perform. create_file(path, content), update_file(path, content), delete_file(path).
            Here is the codebase:
            {get_codebase_contents()}
            Please perform the following operation: {step}

            {prompt_feedback}
            Please don't create incomplete files.
            """
        response = client.inference.chat_completion(
            model_id=MODEL_ID,
            messages=[
                {"role": "system", "content": CODER_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            sampling_params={
                "max_tokens": MAX_TOKENS,
            },
            tools=TOOLS,
            # tool_choice="required",
        )
        message = response.completion_message
        if message.content:
            print("Couldn't run tool - got message: ", message.content[:50] + "...")
        else:
            tool_call = message.tool_calls[0]
            run_tool(tool_call)
    print("\n")

    print(f"{MAGENTA}Reviewer Agent - Reviewing Codebase - Iteration {i}{RESET}")
    response = client.inference.chat_completion(
        model_id=MODEL_ID,
        messages=[
            {"role": "system", "content": REVIEWER_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": f"""
            Here is the full codebase:
            {get_codebase_contents()}
            Please review the codebase and make sure it is correct.
            Please provide a list of changes you would like to make to the codebase.
            """},
        ],
        sampling_params={
            "max_tokens": MAX_TOKENS,
        },
        stream=True,
    )
    review_feedback = ""
    for chunk in response:
        if chunk.event.delta:
            print(chunk.event.delta, end="", flush=True)
            review_feedback += chunk.event.delta
    print("\n")
