import argparse
import json
import os
import datetime

DB_FILE = "tasks.json"

# Auxiliary functions to load and save tasks

def load_tasks():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as file:
            return json.load(file)
    return []

def save_tasks(tasks):
    with open(DB_FILE, "w") as file:
        json.dump(tasks, file, indent=4)

def reindex_tasks(tasks):
    """Re-assigns IDS to tasks based on their position in the list."""
    for index, task in enumerate(tasks, start=1):
        task["id"] = index
    return tasks

# Command implementations

def add_task(description: str):
    tasks = load_tasks()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    tasks.append({
        "id": len(tasks) + 1,
        "description": description, 
        "status": "todo",
        "createdAt": timestamp,
        "updatedAt": None,
    })

    save_tasks(tasks)
    print(f"Task added: {description} (at {timestamp})")

def list_tasks():
    tasks = load_tasks()
    if not tasks:
        print("Your list is empty.")
        return
    print("\n--- YOUR TASKS ---")
    for task in tasks:
        status = "✓" if task.get("status") == "done" else ""
        description = task.get("description", "N/A")

        print(f"{task['id']}. [{status}] {description}")

def update_task(index: int, message: str):
    tasks = load_tasks()
    try:
        tasks[index - 1]["description"] = message
        tasks[index - 1]["updatedAt"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_tasks(tasks)
        print(f"Task #{index} updated to: {message}")
    except IndexError:
        print(f"Error: Task #{index} does not exist.")

def delete_task(task_id: int):
    tasks = load_tasks()

    task_text = tasks[task_id - 1]["description"] if 0 < task_id <= len(tasks) else None
    if task_text is None:
        print(f"Error: Task with ID {task_id} not found.")
        return

    new_tasks = [t for t in tasks if t.get("id") != task_id]

    if len(tasks) == len(new_tasks):
        print(f"Error: Task with ID {task_id} not found.")
        return

    reindexed_tasks = reindex_tasks(new_tasks)
    save_tasks(reindexed_tasks)
    print(f"Task deleted: {task_text}")
    
def main(argv=None):
    parser = argparse.ArgumentParser(description="Agape CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("text", type=str, help="The text of the task to add")

    # List command
    subparsers.add_parser("list", help="List all tasks")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update task text by its index")
    update_parser.add_argument("index", type=int, help="The index of the task to update")
    update_parser.add_argument("message", type=str, help="The new text for the task")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task by its index")
    delete_parser.add_argument("index", type=int, help="The index of the task to delete")

    args = parser.parse_args(argv)
    
    if args.command == "add":
        add_task(args.text)
    elif args.command == "list":
        list_tasks()
    elif args.command == "update":
        update_task(args.index, args.message)
    elif args.command == "delete":
        delete_task(args.index)
    