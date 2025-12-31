import argparse
import json
import os
import dateparser
import shutil
from datetime import datetime, timedelta
from theme import list_tasks, load_tasks, format_due_date

DB_FILE = "tasks.json"
BACKUP_FILE = "tasks.json.bak"

# Auxiliary functions to load and save tasks
def create_backup():
    """Copies current tasks file to a backup before any changes."""
    if os.path.exists(DB_FILE):
        shutil.copy(DB_FILE, BACKUP_FILE)

def undo_action():
    if not os.path.exists(BACKUP_FILE):
        print("No undo history available.")
        return
    
    temp_file = "tasks_temp.json"

    try:
        if os.path.exists(DB_FILE):
            shutil.move(DB_FILE, temp_file)
        
        shutil.move(BACKUP_FILE, DB_FILE)

        if os.path.exists(temp_file):
            shutil.move(temp_file, BACKUP_FILE)
        
        print("Undo successful.")
    except Exception as e:
        print(f"Undo failed: {e}")

def save_tasks(tasks):
    """Saves tasks to json file"""
    with open(DB_FILE, "w") as file:
        json.dump(tasks, file, indent=4)

def reindex_tasks(tasks):
    """Re-assigns IDS to tasks based on their position in the list."""
    for index, task in enumerate(tasks, start=1):
        task["id"] = index
    return tasks
        

# Command implementations

def add_task(description: str, due_string: str = None):
    create_backup()
    tasks = load_tasks()
    now = datetime.now()

    due_at = None
    if due_string:
        parsed_date = dateparser.parse(due_string, settings={'PREFER_DATES_FROM': 'future'})
        if parsed_date:
            due_at = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            print(f"Could not parse date: '{due_string}. Adding without due date.")
    
    tasks.append({
        "id": len(tasks) + 1,
        "description": description, 
        "status": "todo",
        "createdAt": now.strftime("%Y-%m-%d %H:%M:%S"),
        "dueAt": due_at,
        "updatedAt": None,
    })

    save_tasks(tasks)
    print(f"Task added: {description} (at {now})")
    if due_at:
        print(f"    Due: {due_at}")


def update_task(index: int, message: str):
    create_backup()
    tasks = load_tasks()
    try:
        tasks[index - 1]["description"] = message
        tasks[index - 1]["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_tasks(tasks)
        print(f"Task #{index} updated to: {message}")
    except IndexError:
        print(f"Error: Task #{index} does not exist.")

def mark_task(task_id: int, new_status: str):
    create_backup()
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
            task["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break

    if found:
        save_tasks(tasks)
        print(f"Task #{task_id} marked as {target_status}.")
    else:
        print(f"Error: Task with ID {task_id} not found.")  
    

def delete_task(task_id: int = None, all_tasks: bool = False):
    create_backup()

    # Handle Delete All Case
    if all_tasks:
        confirm = input("Are you sure you want to delete ALL tasks? (y/N)\n> ").lower()
        if confirm == 'y':
            save_tasks([])
            print("All tasks have been deleted.")
        else:
            print("Operation cancelled.")
        return
    
    # Safety Check
    if task_id is None:
        print("Error: Please provide a task ID (e.g., agape delete 1) or use --all")
        return

    tasks = load_tasks()

    if not (0 < task_id <= len(tasks)):
        print(f"Error: Task with ID {task_id} not found.")
        return

    task_text = tasks[task_id - 1]["description"] 
    

    new_tasks = [t for t in tasks if t.get("id") != task_id]

    reindexed_tasks = reindex_tasks(new_tasks)
    save_tasks(reindexed_tasks)

    print(f"Task deleted: {task_text}")
    
def main(argv=None):
    parser = argparse.ArgumentParser(description="Agape CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("text", type=str, help="The text of the task to add")
    add_parser.add_argument(
        "-d", "--due", 
        type=str,
        metavar="<date>", 
        help="Natural language due date (e.g. 'tomorrow at 5pm')")

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("-s", "--smart", action="store_true", help="Rank tasks by urgency")

    group = list_parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--done", action="store_true", help="Show only completed tasks")
    group.add_argument("-p", "--progress", action="store_true", help="Show only in-progress tasks")
    group.add_argument("-t", "--todo", action="store_true", help="Show only todo tasks")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update task text by its index")
    update_parser.add_argument("index", type=int, help="The index of the task to update")
    update_parser.add_argument("message", type=str, help="The new text for the task")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete tasks")
    delete_parser.add_argument("index", type=int, nargs='?', help="The index of the task to delete")
    delete_parser.add_argument("-a", "--all", action="store_true", help="Delete all tasks")

    # Mark command
    mark_parser = subparsers.add_parser("mark", help="Change task status by ID")
    mark_parser.add_argument("index", type=int, help="The ID of the task to mark")

    group = mark_parser.add_mutually_exclusive_group()
    group.add_argument("-t", "--todo", action="store_true", help="Mark task as todo")
    group.add_argument("-p", "--progress", action="store_true", help="Mark task as in-progress")
    group.add_argument("-d", "--done", action="store_true", help="Mark task as done")

    # Undo command
    undo_parser = subparsers.add_parser("undo", help="Revert the last destructive action")

    args = parser.parse_args(argv)

    
    
    if args.command == "add":
        add_task(args.text, args.due)
    elif args.command == "list":
        filter_status = None
        if args.done: filter_status = "done"
        elif args.progress: filter_status = "in-progress"
        elif args.todo: filter_status = "todo"
        list_tasks(filter_status, args.smart)
    elif args.command == "update":
        update_task(args.index, args.message)
    elif args.command == "delete":
        delete_task(args.index, args.all)
    elif args.command == "mark":
        status = "todo"  # Default status
        if args.progress: status = "progress"
        if args.done: status = "done"
        mark_task(args.index, status)
    elif args.command == "undo":
        undo_action()
    else:
        parser.print_help()
    return 0
    