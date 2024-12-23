import os
import openai
import json

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


SANDBOX_DIR = os.path.join(os.getcwd(), "sandbox")


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
        print(
            f"Tried to delete file {os.path.join(SANDBOX_DIR, path)} but it does not exist"
        )
        return
    os.remove(os.path.join(SANDBOX_DIR, path))
    print(f"Deleted file {os.path.join(SANDBOX_DIR, path)}")


# def make_dir(path):
#     os.makedirs(os.path.join(SANDBOX_DIR, path), exist_ok=True)
#     print(f"Created directory {os.path.join(SANDBOX_DIR, path)}")

TOOLS = [
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
]


def run_tool(tool_call):
    arguments = json.loads(tool_call.function.arguments)
    if tool_call.function.name == "create_file":
        if "path" not in arguments or "content" not in arguments:
            print(f"create_file, couldn't parse arguments: {arguments}")
            return
        create_file(arguments["path"], arguments["content"])
    elif tool_call.function.name == "update_file":
        if "path" not in arguments or "content" not in arguments:
            print(f"update_file, couldn't parse arguments: {arguments}")
            return
        update_file(arguments["path"], arguments["content"])
    elif tool_call.function.name == "delete_file":
        if "path" not in arguments:
            print(f"delete_file, couldn't parse arguments: {arguments}")
            return
        delete_file(arguments["path"])


from openai import OpenAI
from pydantic import BaseModel
import json

PROGRAM_OBJECTIVE = (
    "a web app that translates text from English to French. Perform the translation on the server side."
)

CODER_AGENT_SYSTEM_PROMPT = f"""
You are a software engineer who is writing code to build a python codebase: {PROGRAM_OBJECTIVE}.
"""

REVIEWER_AGENT_SYSTEM_PROMPT = f"""
You are a senior software engineer who is reviewing the codebase that was created by another software engineer.
The program is {PROGRAM_OBJECTIVE}.
If you think the codebase is good enough to ship, please say LGTM.
Be pragmatic about dependencies - don't import too many.
"""

from typing import List


class Plan(BaseModel):
    steps: List[str]


client = OpenAI(api_key=OPENAI_API_KEY)

if os.path.exists(SANDBOX_DIR):
    # Clear the contents of the directory
    for item in os.listdir(SANDBOX_DIR):
        item_path = os.path.join(SANDBOX_DIR, item)
        if os.path.isfile(item_path):
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            import shutil

            shutil.rmtree(item_path)
else:
    os.makedirs(SANDBOX_DIR)


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


LOOP_LIMIT = 5

BLUE = "\033[94m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
RESET = "\033[0m"

# Coding agent creates a step by step plan
review_feedback = None
for i in range(1, LOOP_LIMIT + 1):
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
        You have 3 different operations you can perform. create_file(path, content), update_file(path, content), delete_file(path)
        Limit your step by step plan to only these operations per step.

        Here is the codebase currently:
        {get_codebase_contents()}

        {prompt_feedback}
        Please ensure there's a README.md file in the root of the codebase that describes the codebase and how to run it.
        Please ensure there's a requirements.txt file in the root of the codebase that describes the dependencies of the codebase.
        """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CODER_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        tools=TOOLS,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "Plan",
                "description": f"A plan to complete the task of creating a codebase that will {PROGRAM_OBJECTIVE}.",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["steps"],
                    "additionalProperties": False,
                },
            },
        },
    )
    plan = json.loads(response.choices[0].message.content)
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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

    print(f"{MAGENTA}Reviewer Agent - Reviewing Codebase - Iteration {i}{RESET}")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
        stream=True,
    )
    review_feedback = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
            review_feedback += chunk.choices[0].delta.content
    print("\n")
