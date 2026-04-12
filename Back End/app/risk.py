import json
import logging

from app.project_plan import fetch_all_work_items
from app.automated_task_assignment import (
    calculate_priority_score,
    validate_and_parse_json,
    get_all_users,
)
from datetime import datetime, timedelta, timezone
from helper.chatgpt import send_chat


def _parse_due_date_for_filter(due_date_str):
    """Azure DevOps returns ISO datetimes; normalize to UTC-aware for comparisons."""
    if not due_date_str:
        return None
    if isinstance(due_date_str, datetime):
        dt = due_date_str
    else:
        s = str(due_date_str).strip()
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def filter_risk_items():
    all_tasks = fetch_all_work_items()
    risk = []
    all_users = get_all_users()
    if isinstance(all_tasks, dict) and "workItems" in all_tasks:
        tasks = all_tasks["workItems"]
    else:
        logging.warning("all_tasks does not contain 'workItems', defaulting to empty list.")
        tasks = []

    tasks = [validate_and_parse_json(task) for task in tasks]

    now = datetime.now(timezone.utc)
    seven_days_from_now = now + timedelta(days=7)

    for task in tasks:
        task["priority_score"] = calculate_priority_score(task)

    # Snapshot before removing items into `risk` (still used for GPT context)
    tasks_snapshot = [dict(t) for t in tasks]

    for task in tasks[:]:
        # project_plan uses due_date (snake_case)
        due_date_str = task.get("due_date") or task.get("dueDate")
        due_date = _parse_due_date_for_filter(due_date_str)
        if due_date is not None:
            try:
                if now <= due_date <= seven_days_from_now:
                    risk.append(task)
                    tasks.remove(task)
            except TypeError:
                logging.warning(f"Due date compare failed for task: {task}")
    
    if tasks:
        average_priority_score = sum(task["priority_score"] for task in tasks) / len(tasks)
        high_priority_tasks = [task for task in tasks if task["priority_score"] > average_priority_score]
        
        for task in high_priority_tasks:
            risk.append(task)
            tasks.remove(task)
    else:
        logging.warning("No tasks available to calculate average priority score.")
    
    schema = {
    "name": "item_list",
    "schema": {
        "type": "object",
        "properties": {
        "items": {
            "type": "array",
            "description": "A list of items containing structured information.",
            "items": {
            "type": "object",
            "properties": {
                "id": {
                "type": "number",
                "description": "Unique identifier for the item."
                },
                "title": {
                "type": "string",
                "description": "Title of the item."
                },
                "state": {
                "type": "string",
                "description": "Current state of the item."
                },
                "assigned_to": {
                "type": "string",
                "description": "User assigned to the item."
                },
                "team_project": {
                "type": "string",
                "description": "The project associated with the item."
                },
                "priority": {
                "type": "number",
                "description": "Priority level of the item."
                },
                "severity": {
                "type": "string",
                "description": "Severity level of the item."
                },
                "due_date": {
                "type": "string",
                "description": "Due date for the item."
                },
                "priority_score": {
                "type": "number",
                "description": "Calculated score based on priority."
                },
                "user_email": {
                "type": "string",
                "description": "Email of the user assigned to the item."
                }
            },
            "required": [
                "id",
                "title",
                "state",
                "assigned_to",
                "team_project",
                "priority",
                "severity",
                "due_date",
                "priority_score",
                "user_email"
            ],
            "additionalProperties": False
            }
        }
        },
        "required": [
        "items"
        ],
        "additionalProperties": False
    },
    "strict": True
    }

    # Avoid huge prompts (token limits): cap how many work items we send to the model
    prompt_tasks = {"workItems": tasks_snapshot}
    max_items = 120
    if len(tasks_snapshot) > max_items:
        prompt_tasks = {
            "workItems": tasks_snapshot[:max_items],
            "_note": f"Showing first {max_items} of {len(tasks_snapshot)} work items. Prefer highest-risk within this set.",
        }

    prompt = (
        f"Analyze the following list of tasks (JSON): {json.dumps(prompt_tasks, default=str)}. "
        f"Each task has a 'priority_score,' calculated based on its priority, severity, and the number of days until the due date. "
        f"Tasks with higher scores are considered more critical. The task list includes items with varying statuses ('new', 'in-progress', 'completed'). "
        f"Your goal is to identify and list the top 15 high-risk tasks based on the following criteria: "
        f"- Tasks with the highest priority scores. "
        f"- Tasks approaching their due dates, especially if their status is 'new' or 'in-progress'. "
        f"- Tasks that have a high priority_score, regardless of their status. "
        f"Match assigned to with the list of all users to get email {json.dumps(all_users, default=str)}. "
        f"Do not include explanations or details outside the required schema."
    )
    

    return send_chat(prompt, context="Task assignment logic", schema=schema)

