import logging
import requests
from requests.auth import HTTPBasicAuth
from helper.chatgpt import send_chat
from app.config import PAT, get_azure_devops_rest_api_url, get_azure_devops_graph_api_url, get_project_name, get_org_name
import json
from datetime import datetime, timezone, timedelta
def get_all_users():
    """
    Fetch and clean all users from Azure DevOps Graph API.
    """
    url = f'{get_azure_devops_graph_api_url()}/users?api-version=7.1-preview.1'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password
    try:
        response = requests.get(url, auth=auth)
        print(response)
        logging.debug(f'Response Status Code: {response.status_code}')
        if response.status_code == 200:
            raw_data = response.json()
            cleaned_data = clean_user_data(raw_data)
            return {"count": len(cleaned_data), "users": cleaned_data}
        else:
            logging.error(f'Failed to fetch data from Azure DevOps: {response.status_code}')
            logging.error(f'Response Content: {response.content.decode()}')
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed: {e}')
        return None

def clean_user_data(raw_data):
    """
    Clean and structure user data from the raw API response.
    """
    users = raw_data.get("value", [])
    cleaned_users = []

    for user in users:
        cleaned_users.append({
            "displayName": user.get("displayName", "N/A"),
            "domain": user.get("domain", "N/A"),
            "mailAddress": user.get("mailAddress", "N/A"),
            "principalName": user.get("principalName", "N/A"),
        })
    return cleaned_users

def fetch_unassigned_tasks():
    """
    Fetch unassigned tasks from Azure DevOps using WIQL.
    """
    url = f'https://dev.azure.com/{get_org_name()}/{get_project_name()}/_apis/wit/wiql?api-version=7.1-preview.2'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password

    # Define the WIQL query
    query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.TeamProject]
        FROM WorkItems
        WHERE [System.AssignedTo] = '' AND [System.TeamProject] = '{get_project_name()}'
        ORDER BY [System.ChangedDate] DESC
        """
    }

    try:
        # Send POST request to execute the WIQL query
        response = requests.post(url, auth=auth, json=query)
        logging.debug(f'WIQL Query URL: {url}')
        logging.debug(f'WIQL Query Payload: {query}')
        logging.debug(f'Response Status Code: {response.status_code}')
        logging.debug(f'Response Content: {response.content.decode()}')
        
        if response.status_code == 200:
            # Extract work item IDs from the response
            work_item_refs = response.json().get('workItems', [])
            work_item_ids = [item['id'] for item in work_item_refs]
            logging.debug(f'Fetched Work Item IDs: {work_item_ids}')
            
            # Fetch full details for each work item in batches of 200
            all_work_items = []
            for i in range(0, len(work_item_ids), 200):
                batch_ids = work_item_ids[i:i+200]
                details_url = f"https://dev.azure.com/{get_org_name()}/{get_project_name()}/_apis/wit/workitemsbatch?api-version=7.1-preview.1"
                details_payload = {"ids": batch_ids}
                details_response = requests.post(details_url, auth=auth, json=details_payload)
                logging.debug(f'Details URL: {details_url}')
                logging.debug(f'Details Payload: {details_payload}')
                logging.debug(f'Details Response Status Code: {details_response.status_code}')
                logging.debug(f'Details Response Content: {details_response.content.decode()}')
                
                if details_response.status_code == 200:
                    all_work_items.extend(details_response.json().get('value', []))
                else:
                    logging.error(f'Failed to fetch work item details: {details_response.status_code}')
                    logging.error(f'Response Content: {details_response.content.decode()}')
                    return None
            
            return {"workItems": all_work_items}
        else:
            logging.error(f'Failed to execute WIQL query: {response.status_code}')
            logging.error(f'Response Content: {response.content.decode()}')
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed: {e}')
        return None

def get_work_item_count_for_user(user_email):
    """
    Get the count of work items assigned to a specific user from Azure DevOps.
    """
    prj = get_project_name()
    url = f'https://dev.azure.com/{get_org_name()}/{get_project_name()}/_apis/wit/wiql?api-version=7.1-preview.2'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password

    # Define the WIQL query
    query = {
        "query": f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.AssignedTo] = '{user_email}'  AND [System.TeamProject] = '{prj}'
        """
    }

    try:
        # Execute the WIQL query
        response = requests.post(url, auth=auth, json=query)
        logging.debug(f'WIQL Query URL: {url}')
        logging.debug(f'WIQL Query Payload: {query}')
        logging.debug(f'Response Status Code: {response.status_code}')
        logging.debug(f'Response Content: {response.content.decode()}')
        
        if response.status_code == 200:
            work_items = response.json().get('workItems', [])
            return len(work_items)
        else:
            logging.error(f'Failed to fetch work item count for {user_email}: {response.status_code}')
            logging.error(f'Response Content: {response.content.decode()}')
            return 0
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed for {user_email}: {e}')
        return 0

def get_work_item_counts_for_all_users():
    """
    Get the work item count for all users retrieved from Azure DevOps.
    """
    # Get all users
    users_data = get_all_users()
    if not users_data or "users" not in users_data:
        logging.error('Failed to fetch users data.')
        return None

    users = users_data["users"]
    user_task_counts = {}

    # Loop through each user and fetch their work item count
    for user in users:
        user_email = user.get("mailAddress")
        if not user_email:
            logging.debug(f'Skipping user {user["displayName"]} (no email address).')
            continue

        task_count = get_work_item_count_for_user(user_email)
        user_task_counts[user_email] = {
            "displayName": user["displayName"],
            "taskCount": task_count
        }
    
    return user_task_counts

def update_work_item_assigned_to(work_item_id, user_email):
    """
    Update the 'Assigned To' field of a work item in Azure DevOps.
    """
    url = f'https://dev.azure.com/{get_org_name()}/{get_project_name()}/_apis/wit/workitems/{work_item_id}?api-version=7.1-preview.3'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password
    headers = {'Content-Type': 'application/json-patch+json'}
    payload = [
        {
            "op": "add",
            "path": "/fields/System.AssignedTo",
            "value": user_email
        }
    ]
    try:
        logging.debug(f'Attempting to update work item {work_item_id} with user {user_email}')
        response = requests.patch(url, auth=auth, headers=headers, json=payload)
        logging.debug(f'Update Work Item URL: {url}')
        logging.debug(f'Update Work Item Headers: {headers}')
        logging.debug(f'Update Work Item Payload: {payload}')
        logging.debug(f'Response Status Code: {response.status_code}')
        logging.debug(f'Response Content: {response.content.decode()}')

        if response.status_code == 200:
            logging.info(f'Successfully updated work item {work_item_id} to {user_email}')
            return response.json()
        else:
            logging.error(f'Failed to update work item {work_item_id}: {response.status_code}')
            logging.error(f'Response Content: {response.content.decode()}')
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed for work item {work_item_id}: {e}')
        return None
    

def calculate_priority_score(task):
    """
    Calculates a priority score for a task based on priority, severity, and days till due date.
    Handles missing or empty values by assigning default values.
    :param task: Dictionary representing a task.
    :return: Computed priority score (higher is more critical).
    """
    logging.debug(f'Calculating priority score for task: {task}')
    
    # Extract components with defaults for missing values
    priority = task.get("priority", 5)  # Default to lowest priority (5)
    severity_str = task.get("severity", "3 - Medium")
    due_date_str = task.get("due_date", None)

    # Handle priority as integer (Azure may return int, string "2", or "2 - High")
    if isinstance(priority, str):
        try:
            priority = int(priority.strip().split()[0])
        except (ValueError, IndexError):
            priority = 5
    if not isinstance(priority, int) or priority < 1 or priority > 5:
        priority = 5  # Default to lowest priority if invalid

    # Extract severity as an integer
    try:
        severity = int(severity_str.split(" - ")[0])  # Extract numeric part
    except (ValueError, AttributeError):
        severity = 3  # Default to medium severity if invalid or missing

    # Calculate days until due date
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))  # Convert to aware datetime
        except ValueError:
            due_date = datetime.now(timezone.utc) + timedelta(days=30)  # Default to 30 days from now if invalid
    else:
        due_date = datetime.now(timezone.utc) + timedelta(days=30)  # Default to 30 days from now if missing

    # Calculate days remaining
    current_time = datetime.now(timezone.utc)  # Use timezone-aware current UTC time
    days_until_due = max((due_date - current_time).days, 0)

    # Calculate the priority score (higher score means higher urgency)
    score = (5 - priority) * 2 + (5 - severity) * 3 + max(0, 30 - days_until_due)
    logging.debug(f'Priority score for task {task["id"] if "id" in task else "unknown"}: {score}')
    return score


def calculate_total_priority_by_user(all_tasks, assignments):
    """
    Calculates the total priority score for each user based on their assigned tasks.
    :param all_tasks: List of all tasks with their current priority scores.
    :param assignments: Dictionary mapping users (emails) to their assigned tasks.
    :return: A dictionary with users' emails as keys and their total priority scores as values.
    """
    total_priority_by_user = {}
    
    # Initialize priority scores for all users
    for user in assignments.keys():
        total_priority_by_user[user] = 0

    # Sum up priority scores for each user's tasks
    for task in all_tasks:
        assigned_user = task.get("assigned_to")
        if assigned_user in total_priority_by_user:
            total_priority_by_user[assigned_user] += task.get("priority_score", 0)

    return total_priority_by_user

def validate_and_parse_json(data):
    """
    Validates and parses a JSON string into a dictionary. If invalid, returns an empty dictionary.
    :param data: The JSON string or dictionary.
    :return: A dictionary parsed from the JSON string or the original dictionary.
    """
    if isinstance(data, dict):  # If it's already a dictionary, return it as is
        return data
    elif isinstance(data, str) and data.strip():  # If it's a string, try parsing it as JSON
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logging.warning(f"Invalid JSON string: {data}. Defaulting to empty dictionary.")
            return {}
    else:
        logging.warning(f"Unexpected data type: {type(data)}. Defaulting to empty dictionary.")
        return {}

def generate_gpt_task_assignment(unassigned_work_items, all_tasks):
    """
    Generates task assignments using GPT-4, considering a calculated priority score.
    :param unassigned_work_items: List of unassigned work items.
    :param all_tasks: Dictionary containing tasks under the 'workItems' key.
    :return: Generated task assignments as a string.
    """
    logging.debug(f'Generating GPT task assignment for unassigned work items: {unassigned_work_items}')
    logging.debug(f'Raw all_tasks input: {all_tasks}')
    
    # Extract the list of tasks from 'workItems'
    if isinstance(all_tasks, dict) and "workItems" in all_tasks:
        tasks = all_tasks["workItems"]
    else:
        logging.warning("all_tasks does not contain 'workItems', defaulting to empty list.")
        tasks = []

    if isinstance(unassigned_work_items, dict) and "workItems" in unassigned_work_items:
        unassigned_work_items = unassigned_work_items["workItems"]
    else:
        logging.warning("unassigned_work_items does not contain 'workItems', defaulting to empty list.")
        unassigned_work_items = []

    print(f"Extracted tasks from workItems: {tasks}")

    # Ensure all tasks are dictionaries
    tasks = [validate_and_parse_json(task) for task in tasks]
    unassigned_work_items = [validate_and_parse_json(item) for item in unassigned_work_items]

    print(f"Validated all_tasks: {tasks}")

    # Calculate priority scores for all tasks
    for task in tasks:
        task["priority_score"] = calculate_priority_score(task)

    print(f"All tasks after calculating priority scores: {tasks}")

    # Assign default values instead of removing fields
    tasks_with_defaults = []
    for task in tasks:
        # Create a new task dictionary with defaults assigned
        task_with_defaults = {
            "id": task.get("id", None),
            "title": task.get("title", "No Title"),
            "state": task.get("state", "New"),
            "assigned_to": task.get("assigned_to", "Unassigned"),
            "team_project": task.get("team_project", "Unknown Project"),
            "priority_score": task.get("priority_score", 0),  # Keep calculated score
        }
        tasks_with_defaults.append(task_with_defaults)

    print(f"Tasks with defaults applied: {tasks_with_defaults}")

    # Compute user workload and total priority score
    assignment_count_per_person = get_work_item_counts_for_all_users()
    total_priority_by_user = calculate_total_priority_by_user(tasks_with_defaults, assignment_count_per_person)

    print(f"Assignment count per person: {assignment_count_per_person}")
    print(f"Total priority score by user: {total_priority_by_user}")

    prompt = (
        f"Analyze the following unassigned work item(s): {unassigned_work_items}. "
        f"Current task assignments are as follows: {assignment_count_per_person}. "
        f"Each task in {tasks_with_defaults} has a 'priority_score', calculated based on its priority, severity, "
        f"and the number of days until the due date. Higher scores indicate greater urgency and importance. "
        f"The total priority score for each user is as follows: {total_priority_by_user}. "
        f"Your task is to recommend 3 individuals to be assigned the unassigned tasks, ensuring: "
        f"- The first two recommendations are balanced to prevent overloading any one person. "
        f"- Assignments align with expertise based on current tasks. "
        f"- The third recommendation should be someone with a lot of tasks to ensure critical tasks are among more seniors (Mention that user balances lots of task showing capability to handle critical taks). "
        f"Take into account the total priority score of tasks already assigned to each person, "
        f"so that assignments are equitable based on both task count and overall priority importance. "
        f"Provide only the email of each recommended individual and a concise explanation of your reasoning, "
        f"which must include task count, total priority importance, and priority score considerations. Do not include anything else in your response."
    )


    print(f"Generated prompt for GPT: {prompt}")

    schema = {
        "name": "task_assignment_response",
        "schema": {
            "type": "object",
            "properties": {
                "assignments": {
                    "type": "array",
                    "description": "List of individuals assigned to tasks",
                    "items": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email of the user selected for the assignment"
                            },
                            "display_name": {
                                "type": "string",
                                "description": "Display name of the user selected for the assignment"
                            },
                            "reason": {
                                "type": "string",
                                "description": "A short explanation of why the user is the best fit for the task"
                            }
                        },
                        "required": [
                            "email",
                            "display_name",
                            "reason"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            "required": [
                "assignments"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
    
    return send_chat(prompt, context="Task assignment logic", model="gpt-4o-mini", schema=schema)
