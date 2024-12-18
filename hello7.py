import os
from llama_stack_client import LlamaStackClient
from tools import SANDBOX_DIR, TOOLS, run_tool
import json

MODEL_ID = "meta-llama/Llama-3.1-405B-Instruct-FP8"

LOOP_LIMIT = 5

# response = client.inference.chat_completion(
#     model_id=model_id,
#     messages=[{"role": "user", "content": "What is the capital of France?"}],
# )

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
for i in range(LOOP_LIMIT):
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
        You have 3 different operations you can perform. create_file(path, content), update_file(path, content), delete_file(path)
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
        # tools=TOOLS,
    )
    plan = json.loads(response.completion_message.content)
    for step_idx, step in enumerate(plan["steps"]):
        print(f"{step_idx + 1}. {step}")
    print("\n")

    # Coding agent executes the plan
    print(f"{BLUE}Coder Agent - Executing Plan - Iteration {i}{RESET}")
    for step in plan["steps"]:
        prompt = f"""
            You have 3 different operations you can perform. create_file(path, content), update_file(path, content), delete_file(path).
            Here is the codebase:
            {get_codebase_contents()}
            Please perform the following operation: {step}
            """
        response = client.inference.chat_completion(
            model_id=MODEL_ID,
            messages=[
                {"role": "system", "content": CODER_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=TOOLS,
        )
        message = response.choices[0].message
        if message.content:
            print("Not enough information to run tool: ", message.content)
        else:
            tool_call = message.tool_calls[0]
            run_tool(tool_call)
    print("\n")

    # print(f"{MAGENTA}Reviewer Agent - Reviewing Codebase - Iteration {i}{RESET}")
    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "system", "content": REVIEWER_AGENT_SYSTEM_PROMPT},
    #         {"role": "user", "content": f"""
    #         Here is the full codebase:
    #         {get_codebase_contents()}
    #         Please review the codebase and make sure it is correct.
    #         Please provide a list of changes you would like to make to the codebase.
    #         """},
    #     ],
    #     stream=True,
    # )
    # review_feedback = ""
    # for chunk in response:
    #     if chunk.choices[0].delta.content:
    #         print(chunk.choices[0].delta.content, end="", flush=True)
    #         review_feedback += chunk.choices[0].delta.content
    # print("\n")