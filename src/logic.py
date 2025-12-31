import argparse
import json
import os
import dateparser
import shutil
from datetime import datetime, timedelta

DB_FILE = "tasks.json"
BACKUP_FILE = "tasks.json.bak"

# Auxiliary functions to load and save tasks
def create_backup():
    """Copies current tasks file to a backup before any changes."""
    if os.path.exists(DB_FILE):
        shutil.copy(DB_FILE, BACKUP_FILE)

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

def format_due_date(due_at_str):
    if not due_at_str:
        return ""

    due_at = datetime.strptime(due_at_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    diff = due_at - now

    if diff.total_seconds() < 0:
        days = abs(diff.days)
        return f" (Overdue by {days}d)" if days > 0 else " (Overdue)"
    elif diff.total_seconds() < 60:
        return f" (Due in the next minute!)"
    elif diff.total_seconds() < 3600:
        return f" (Due in the next hour!)"
    elif diff.total_seconds() < 86400:
        hours = diff.seconds // 3600
        return f" (Due in the next {hours}h)"
    else:
        if diff.days > 0:
            return f" (Due in {diff.days}d)"

def calculate_urgency(task):
    """Calculates a numeric score to rank tasks based on relative importance."""
    score = 0
    now = datetime.now()

    if task.get("status") == "done":
        return -1000
    if task.get("status") == "in-progress":
        score += 500
    
    if task.get("dueAt"):
        due_date = datetime.strptime(task["dueAt"], "%Y-%m-%d %H:%M:%S")
        time_diff = due_date - now

        if time_diff.total_seconds() < 0:
            score += 2000  # OVERDUE: Highest priority
        elif time_diff < timedelta(hours=24):
            score += 1000  # DUE SOON: High priority
        elif time_diff < timedelta(days=3):
            score += 500   # UPCOMING: Medium priority
    
    created_at = datetime.strptime(task["createdAt"], "%Y-%m-%d %H:%M:%S")
    recency_bonus = (created_at - datetime(2025, 1, 1)).total_seconds() / 100000
    score += recency_bonus

    return score
        

# Command implementations

def add_task(description: str, due_string: str = None):
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

def list_tasks(filter_status=None, smart=False):
    tasks = load_tasks()

    if filter_status:
        tasks = [t for t in tasks if t.get("status") == filter_status]

    if smart:
        tasks.sort(key=calculate_urgency, reverse=True)
        header = "--- SMART RANKED TASKS (Urgency Logic Applied) ---"
    else:
        header = f"--- {filter_status.upper()} TASKS ---" if filter_status else "--- TASKS ---"

    if not tasks:
        msg = f"No tasks found with status '{filter_status}'." if filter_status else "Nothing to do right now. Relax and enjoy yourself!"
        print(msg)
        return

    
    print(f"\n{header}")

    todo_count = 0
    in_progress_count = 0
    done_count = 0
    overdue_count = 0
    total_tasks_count = 0

    for task in tasks:
        due_at_str = task.get("dueAt")
        due_date = None
        if due_at_str:
            due_date = datetime.strptime(due_at_str, "%Y-%m-%d %H:%M:%S")

        t_id = task.get("id", "?")
        
        if due_date and due_date < datetime.now():
            overdue_count += 1
        if task["status"] == "todo":
            status = ""
            todo_count += 1
        elif task["status"] == "in-progress":
            status = "○"
            in_progress_count += 1
        elif task["status"] == "done":
            status = "✓"
            done_count += 1
        
        total_tasks_count += 1

        label = ""
        if smart and task.get("status") != "done":
            due_at = task.get("dueAt")
            if due_at and datetime.strptime(due_at, "%Y-%m-%d %H:%M:%S") < datetime.now():
                label = "🔥 OVERDUE"
            elif task.get("status") == "in-progress":
                label = "⚡ ACTIVE"
            
        description = task.get("description", "N/A")

        print(f"{t_id}. [{label if label else status}] {description}{format_due_date(task.get('dueAt'))}")
    
    if overdue_count == total_tasks_count:
        print("\nYour task is overdue. Better get to work!")
    elif overdue_count > 2:
        print("\nSeveral tasks are overude. We should prioritize.")
    elif todo_count == total_tasks_count:
        print("\nPlenty of things to do. Let's get started with something!")
    elif in_progress_count > 1:
        print("\nMultiple tasks in progress. Don't spread yourself thin!")
    elif done_count == total_tasks_count:
        print("\nLook at your efficiency! Well done!")

def update_task(index: int, message: str):
    tasks = load_tasks()
    try:
        tasks[index - 1]["description"] = message
        tasks[index - 1]["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            task["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break

    if found:
        save_tasks(tasks)
        print(f"Task #{task_id} marked as {target_status}.")
    else:
        print(f"Error: Task with ID {task_id} not found.")  
    

def delete_task(task_id: int = None, all_tasks: bool = False):
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
    else:
        parser.print_help()
    return 0
    