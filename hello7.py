import os
from llama_stack_client import LlamaStackClient
from tools import SANDBOX_DIR

model_id = "meta-llama/Llama-3.1-405B-Instruct-FP8"

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