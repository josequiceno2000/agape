import argparse
import json
import os

DB_FILE = "tasks.json"

def add_task(text: str):
    # 1. READ: Get existing tasks from the JSON file.
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as file:
            tasks = json.load(file)
    else:
        tasks = []

    # 2. MODIFY: Add the new task to the list.
    tasks.append({"text": text, "completed": False})

    # 3. WRITE: Save the updated list back to the JSON file.
    with open(DB_FILE, "w") as file:
        json.dump(tasks, file, indent=4)    
    
    print(f"Added task: {text}")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Agape CLI Tool")

    subparsers = parser.add_subparsers(dest="command")
    add_parser = subparsers.add_parser("add", help="Add a new task")

    add_parser.add_argument("text", type=str, help="The text of the task to add")

    args = parser.parse_args(argv)
    
    if args.command == "add":
        add_task(args.text)
    