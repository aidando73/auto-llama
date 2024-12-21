import os
import json

SANDBOX_DIR = os.path.join(os.getcwd(), "sandbox")

TOOLS = [
    {
        "tool_name": "create_file",
        "description": "Create a file with the given name and content. If there are any directories that don't exist, create them.",
        "parameters": {
            "path": {
                "param_type": "string",
                "description": "The relative path to the file to create",
                "required": True,
            },
            "content": {
                "param_type": "string",
                "description": "The content of the file to create",
                "required": True,
            },
        },
    },
    {
        "tool_name": "update_file",
        "description": "Update a file with the given name and content. If the file does not exist, create it.",
        "parameters": {
            "path": {
                "param_type": "string",
                "description": "The relative path to the file to update",
                "required": True,
            },
            "content": {
                "param_type": "string",
                "description": "The content of the file to update",
                "required": True,
            },
        },
    },
    {
        "tool_name": "delete_file",
        "description": "Delete a file with the given path. If the file does not exist, do nothing.",
        "parameters": {
            "path": {
                "param_type": "string",
                "description": "The relative path to the file to delete",
                "required": True,
            },
        },
    },
]


def create_file(path, content):
    if not path:
        print("create_file, couldn't parse arguments: {arguments}")
        return

    # Ensure path doesn't try to escape sandbox directory
    normalized_path = os.path.normpath(path)
    if normalized_path.startswith('..') or normalized_path.startswith('/'):
        print(f"create_file: Path {path} attempts to escape sandbox directory. Skipping.")
        return

    # Hack because llama sometimes escapes newlines
    content = content.replace("\\n", "\n")

    # Create any directories that don't exist
    try:
        os.makedirs(os.path.dirname(os.path.join(SANDBOX_DIR, path)), exist_ok=True)
    except Exception as e:
        print(f"create_file, error creating parent directories: {path}. Skipping.")
        return

    # Write to file
    with open(os.path.join(SANDBOX_DIR, path), "w") as f:
        f.write(content)
    print(f"Created file {os.path.join(SANDBOX_DIR, path)}")

def update_file(path, content):
    if not path:
        print("update_file, couldn't parse arguments: {arguments}")
        return
    
    # Ensure path doesn't try to escape sandbox directory
    normalized_path = os.path.normpath(path)
    if normalized_path.startswith('..') or normalized_path.startswith('/'):
        print(f"update_file: Path {path} attempts to escape sandbox directory. Skipping.")
        return

    # Hack because llama sometimes escapes newlines
    content = content.replace("\\n", "\n")

    # Create any directories that don't exist
    try:
        os.makedirs(os.path.dirname(os.path.join(SANDBOX_DIR, path)), exist_ok=True)
    except Exception as e:
        print(f"update_file, error creating parent directories: {path}. Skipping.")
        return

    # Write to file
    with open(os.path.join(SANDBOX_DIR, path), "w") as f:
        f.write(content)
    print(f"Updated file {os.path.join(SANDBOX_DIR, path)}")

def delete_file(path):
    # Ensure path doesn't try to escape sandbox directory
    normalized_path = os.path.normpath(path)
    if normalized_path.startswith('..') or normalized_path.startswith('/'):
        print(f"delete_file: Path {path} attempts to escape sandbox directory. Skipping.")
        return

    # If the file doesn't exist, don't do anything
    if not os.path.exists(os.path.join(SANDBOX_DIR, path)):
        print(
            f"Tried to delete file {os.path.join(SANDBOX_DIR, path)} but it does not exist"
        )
        return
    os.remove(os.path.join(SANDBOX_DIR, path))
    print(f"Deleted file {os.path.join(SANDBOX_DIR, path)}")


def run_tool(tool_call):
    arguments = tool_call.arguments
    if tool_call.tool_name == "create_file":
        if "path" not in arguments or "content" not in arguments:
            print(f"create_file, couldn't parse arguments: {arguments}")
            return
        create_file(arguments["path"], arguments["content"])
    elif tool_call.tool_name == "update_file":
        # Does the same thing as create_file - but nice to have a separate function for updating files
        # So the LLM has the option to update files if it wants to - if that makes more sense than creating a new file
        if "path" not in arguments or "content" not in arguments:
            print(f"update_file, couldn't parse arguments: {arguments}")
            return
        update_file(arguments["path"], arguments["content"])
    elif tool_call.tool_name == "delete_file":
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
