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

def list_tasks(filter_status=None):
    tasks = load_tasks()

    if filter_status:
        tasks = [t for t in tasks if t.get("status") == filter_status]

    if not tasks:
        msg = f"No tasks found with status '{filter_status}'." if filter_status else "Your list is empty."
        print(msg)
        return

    header = f"--- {filter_status.upper()} TASKS ---" if filter_status else "--- TASKS ---"
    print(header)

    for task in tasks:
        if task["status"] == "todo":
            status = ""
        elif task["status"] == "in-progress":
            status = "○"
        elif task["status"] == "done":
            status = "✓"
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

def mark_task(task_id: int, new_status: str):
    tasks = load_tasks()
    status_map = {
        "todo": "todo",
        "progress": "in-progress",
        "done": "done"
    }

    target_status = status_map.get(new_status.lower())
    if not target_status:
        print(f"Error: Invalid status '{new_status}'. Valid statuses are: todo, progress, done.")
        return
    
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = target_status
            task["updatedAt"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break

    if found:
        save_tasks(tasks)
        print(f"Task #{task_id} marked as {target_status}.")
    else:
        print(f"Error: Task with ID {task_id} not found.")  
    

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
    list_parser = subparsers.add_parser("list", help="List tasks")

    group = list_parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--done", action="store_true", help="Show only completed tasks")
    group.add_argument("-p", "--progress", action="store_true", help="Show only in-progress tasks")
    group.add_argument("-t", "--todo", action="store_true", help="Show only todo tasks")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update task text by its index")
    update_parser.add_argument("index", type=int, help="The index of the task to update")
    update_parser.add_argument("message", type=str, help="The new text for the task")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task by its index")
    delete_parser.add_argument("index", type=int, help="The index of the task to delete")

    # Mark command
    mark_parser = subparsers.add_parser("mark", help="Change task status by ID")
    mark_parser.add_argument("index", type=int, help="The ID of the task to mark")

    group = mark_parser.add_mutually_exclusive_group()
    group.add_argument("-t", "--todo", action="store_true", help="Mark task as todo")
    group.add_argument("-p", "--progress", action="store_true", help="Mark task as in-progress")
    group.add_argument("-d", "--done", action="store_true", help="Mark task as done")

    args = parser.parse_args(argv)
    
    if args.command == "add":
        add_task(args.text)
    elif args.command == "list":
        filter_status = None
        if args.done:
            filter_status = "done"
        elif args.progress:
            filter_status = "in-progress"
        elif args.todo:
            filter_status = "todo"
        list_tasks(filter_status)
    elif args.command == "update":
        update_task(args.index, args.message)
    elif args.command == "delete":
        delete_task(args.index)
    elif args.command == "mark":
        status = "todo"  # Default status
        if args.progress: status = "progress"
        if args.done: status = "done"
        mark_task(args.index, status)
    else:
        parser.print_help()
    return 0
    