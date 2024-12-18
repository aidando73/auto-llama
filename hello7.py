import os
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

# List available models
models = client.models.list()

# for model in models:
#     print(model)

model_id = "meta-llama/Llama-3.1-405B-Instruct-FP8"

response = client.inference.chat_completion(
    model_id=model_id,
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)

print(response)