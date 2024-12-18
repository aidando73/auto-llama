import os
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