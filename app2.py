import os
from llama_stack_client import LlamaStackClient
import json

SANDBOX_DIR = "/Users/aidand/dev/auto-llama/sandbox"

def create_file(path, content):
    # Create any directories that don't exist
    os.makedirs(os.path.dirname(os.path.join(SANDBOX_DIR, path)), exist_ok=True)
    with open(os.path.join(SANDBOX_DIR, path), "w") as f:
        f.write(content)
    print(f"Created file {os.path.join(SANDBOX_DIR, path)}")

# Does the same thing as create_file - but nice to have a separate function for updating files
# So the LLM has the option to update files if it wants to - if that makes more sense than creating a new file
def update_file(path, content):
    os.makedirs(os.path.dirname(os.path.join(SANDBOX_DIR, path)), exist_ok=True)
    with open(os.path.join(SANDBOX_DIR, path), "w") as f:
        f.write(content)
    print(f"Updated file {os.path.join(SANDBOX_DIR, path)}")

def delete_file(path):
    # If the file doesn't exist, don't do anything
    if not os.path.exists(os.path.join(SANDBOX_DIR, path)):
        print(f"Tried to delete file {os.path.join(SANDBOX_DIR, path)} but it does not exist")
        return
    os.remove(os.path.join(SANDBOX_DIR, path))
    print(f"Deleted file {os.path.join(SANDBOX_DIR, path)}")

def run_tool(tool_call):
    arguments = json.loads(tool_call["function"]["arguments"])
    if tool_call["function"]["name"] == "create_file":
        if "path" not in arguments or "content" not in arguments:
            print(f"create_file, couldn't parse arguments: {arguments}")
            return
        create_file(arguments["path"], arguments["content"])
    elif tool_call["function"]["name"] == "update_file":
        if "path" not in arguments or "content" not in arguments:
            print(f"update_file, couldn't parse arguments: {arguments}")
            return
        update_file(arguments["path"], arguments["content"])
    elif tool_call["function"]["name"] == "delete_file":
        if "path" not in arguments:
            print(f"delete_file, couldn't parse arguments: {arguments}")
            return
        delete_file(arguments["path"])


# MODEL_ID = "meta-llama/Llama-3.1-405B-Instruct-FP8"
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"

# Number of code review cycles
CODE_REVIEW_CYCLES = 5

# No limit on output tokens
MAX_TOKENS = 200_000


PROGRAM_OBJECTIVE = (
    "a web server that has an API endpoint that translates text from English to French."
)

CODER_AGENT_SYSTEM_PROMPT = f"""
You are a software engineer who is writing code to build a python codebase: {PROGRAM_OBJECTIVE}.
"""

REVIEWER_AGENT_SYSTEM_PROMPT = f"""
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

    prompt = f"""
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
                "properties": {"steps": {"type": "array", "items": {"type": "string"}}},
                "required": ["steps"],
                "additionalProperties": False,
            },
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
            Please don't escape \n or \t in the content you are writing to a file and please don't create incomplete files.
            """
        # response = client.inference.chat_completion(
        #     model_id=MODEL_ID,
        #     messages=[
        #         {"role": "system", "content": CODER_AGENT_SYSTEM_PROMPT},
        #         {"role": "user", "content": prompt},
        #     ],
        #     sampling_params={
        #         "max_tokens": MAX_TOKENS,
        #     },
        #     tools=TOOLS,
        # )
        # message = response.completion_message

        import requests
        import json

        # Hitting the Fireworks API directly.
        # Llama-stack doesn't handle 'required' fields in tool calls.
        url = "https://api.fireworks.ai/inference/v1/chat/completions"
        payload = {
            "model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "max_tokens": MAX_TOKENS,
            "top_p": 1,
            "top_k": 40,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "temperature": 0.6,
            "messages": [
                {"role": "system", "content": CODER_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "tool_choice": "any",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "create_file",
                        "description": "Create a file with the given name and content. If there are any directories that don't exist, create them.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "The relative path to the file to create",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The content of the file to create",
                                },
                            },
                            "required": ["path", "content"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "update_file",
                        "description": "Update a file with the given name and content. If the file does not exist, create it.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "The relative path to the file to update",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The content of the file to update",
                                },
                            },
                            "required": ["path", "content"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "delete_file",
                        "description": "Delete a file with the given path. If the file does not exist, do nothing.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "The relative path to the file to delete",
                                },
                            },
                            "required": ["path"],
                        },
                    },
                },
            ],
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['FIREWORKS_API_KEY']}",
        }
        resp = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        print(resp.json())
        message = resp.json()["choices"][0]["message"]
        print(message)
        if "content" in message:
            print("Not enough information to run tool: ", message["content"][:100] + "...")
        else:
            tool_call = message["tool_calls"][0]
            run_tool(tool_call)
    print("\n")

    print(f"{MAGENTA}Reviewer Agent - Reviewing Codebase - Iteration {i}{RESET}")
    response = client.inference.chat_completion(
        model_id=MODEL_ID,
        messages=[
            {"role": "system", "content": REVIEWER_AGENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
            Here is the full codebase:
            {get_codebase_contents()}
            Please review the codebase and make sure it is correct.
            Please provide a list of changes you would like to make to the codebase.
            """,
            },
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