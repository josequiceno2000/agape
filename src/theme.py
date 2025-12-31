import os
import textwrap
import shutil
import json
from datetime import datetime, timedelta

DB_FILE = "tasks.json"
BACKUP_FILE = "tasks.json.bak"

# --- THEME SYSTEM ---
CLR_RESET = "\033[0m"
CLR_BOLD  = "\033[1m"
CLR_DIM   = "\033[2m"
CLR_RED   = "\033[31m"
CLR_GREEN = "\033[32m"
CLR_CYAN  = "\033[36m"

# Icons & Status Labels
STATUS_THEME = {
    "todo":        {"icon": "☐", "label": "TODO",     "color": CLR_RESET},
    "in-progress": {"icon": "◐", "label": "ACTIVE",   "color": CLR_CYAN},
    "done":        {"icon": "✓", "label": "",     "color": CLR_DIM + CLR_GREEN},
}

def load_tasks():
    """Loads all tasks from tasks.json file"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as file:
            return json.load(file)
    return []

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

def human_time(date_str):
    """Displays time in human-legible format"""
    if not date_str: return ""
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    diff = datetime.now() - dt

    if diff.total_seconds() < 60: return "just now"
    if diff.total_seconds() < 3600: return f"{int(diff.total_seconds() // 60)}m ago"
    if diff.total_seconds() < 86400: return f"{int(diff.total_seconds() // 3600)}h ago"
    return dt.strftime("%b %d")

def list_tasks(filter_status=None, smart=False):
    tasks = load_tasks()
    raw_width = shutil.get_terminal_size((80, 20)).columns
    term_width = min(raw_width, 100)

    if filter_status:
        tasks = [t for t in tasks if t.get("status") == filter_status]
    if smart: tasks.sort(key=calculate_urgency, reverse=True)

    # --- HEADER ---
    title = f"AGAPE - {'SMART' if smart else 'ALL'} TASKS"
    print(f"\n{CLR_BOLD}{title}{CLR_RESET}")
    print(f"{CLR_DIM}{len(tasks)} tasks total{CLR_RESET}\n")

    # Column Headers
    header = f"{'ID':<4} {'STATUS':<12} {'TASK'}"
    print(f"{CLR_DIM}{header}{CLR_RESET}")
    print(f"{CLR_DIM}{'─' * term_width}{CLR_RESET}")

    if not tasks:
        print(f"{CLR_DIM}Nothing to show. Relax and enjoy.{CLR_RESET}")
        return
    
    # --- TASK ROWS ---
    active_count = 0
    overdue_count = 0
    done_count = 0
    total_count = 0

    for t in tasks:
        status = t.get("status", "todo")
        style = STATUS_THEME.get(status)

        if status == "in-progress":
            active_count += 1
        elif status == "done":
            done_count += 1
        
        due_label = format_due_date(t.get("dueAt"))
        if status != "done" and "Overdue" in due_label:
            overdue_count += 1
        
        time_str = human_time(t.get('createdAt'))
        time_info = f"{CLR_DIM} · {time_str}{CLR_RESET}"

        # Column 1 & 2: ID and Status
        id_str = f"{t['id']:<4}"
        status_str = f"{style['color']}{style['icon']} {style['label']:<9}{CLR_RESET}"
        
        # Column 3: Description (Dynamic Width)
        meta_padding = 15
        available_width = term_width - 25 - meta_padding
        desc = textwrap.shorten(t['description'], width=available_width, placeholder="…")
        
        # Final Assemble
        row = f"{id_str} {status_str} {desc}{time_info}"
        print(row)

        total_count += 1

    # --- FOOTER ---
    print(f"{CLR_DIM}{'─' * term_width}{CLR_RESET}")
    
    footer_parts = [f"{len(tasks)} total"]
    if done_count == total_count:
        footer_parts.append(f"{CLR_GREEN}all complete{CLR_RESET}")
    else:
        if done_count > 0:
            footer_parts.append(f"{CLR_GREEN}{done_count} done{CLR_RESET}")
        if active_count > 0:
            footer_parts.append(f"{CLR_CYAN}{active_count} active{CLR_RESET}")
        if overdue_count > 0:
            footer_parts.append(f"{CLR_RED}{overdue_count} overdue{CLR_RESET}")

    footer_text = f" {CLR_DIM} · {CLR_RESET}".join(footer_parts)
    print(f"{CLR_DIM}{footer_text}{CLR_RESET}\n")
