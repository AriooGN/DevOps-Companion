from flask import Flask, jsonify, request, send_file
from app.automated_task_assignment import get_all_users, fetch_unassigned_tasks, get_work_item_counts_for_all_users, generate_gpt_task_assignment, update_work_item_assigned_to
from app.status_report import fetch_pending_tasks
from flask_cors import CORS
from app.stats import count_work_items_by_state, count_work_items_by_assignment, count_work_items_by_type
from app.project_plan import fetch_all_work_items,generate_ms_project_plan
from app.config import (
    BACKEND_ROOT,
    set_jwt_token,
    set_project_name,
    get_project_name,
    get_jwt_token,
)
from app.risk import filter_risk_items
from helper.outlook import OutlookEmailSender
from app.status_report import organize_tasks_by_due_date
from helper.chatgpt import generate_gpt_email,generate_subject_line
from app.login import get_current_project, fetch_user_projects
import json
import os
from chatbot.chat_handler import ChatHandler

app = Flask(__name__)

# localhost vs 127.0.0.1 are different origins — allow both for Next.js dev
_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
CORS(
    app,
    origins=_CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    expose_headers=["Content-Disposition"],
)


def _corsify_response(resp):
    """Ensure dev origins get ACAO when Flask-CORS does not attach (e.g. some error paths)."""
    from flask import request as _req

    origin = _req.headers.get("Origin")
    if origin in _CORS_ORIGINS:
        resp.headers.setdefault("Access-Control-Allow-Origin", origin)
        resp.headers.setdefault("Access-Control-Allow-Credentials", "true")
    return resp


@app.after_request
def _after_request_cors(resp):
    return _corsify_response(resp)


@app.errorhandler(Exception)
def _unhandled_exception(e):
    from werkzeug.exceptions import HTTPException

    if isinstance(e, HTTPException):
        r = e.get_response()
        return _corsify_response(r)
    import traceback

    traceback.print_exc()
    r = jsonify({"error": str(e)})
    r.status_code = 500
    return _corsify_response(r), 500


chat_handler = ChatHandler()

def update_project_name(new_project_name):
    """Persist active project to Back End/.env and in-memory config."""
    env_path = BACKEND_ROOT / ".env"
    key = "AZURE_DEVOPS_PROJECT="
    if env_path.is_file():
        raw = env_path.read_text(encoding="utf-8")
        lines = raw.splitlines(keepends=True)
        found = False
        out = []
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(key) or stripped.startswith("PROJECT_NAME="):
                out.append(f"AZURE_DEVOPS_PROJECT={new_project_name}\n")
                found = True
            else:
                out.append(line)
        if not found:
            if out and not out[-1].endswith("\n"):
                out[-1] = out[-1] + "\n"
            out.append(f"AZURE_DEVOPS_PROJECT={new_project_name}\n")
        env_path.write_text("".join(out), encoding="utf-8")
    set_project_name(new_project_name)
    os.environ["AZURE_DEVOPS_PROJECT"] = new_project_name
@app.route('/api/automated_task_assignment/fetch_allusers', methods=['GET'])
def fetch_users():
    """
    Flask route to fetch and return all users as JSON.
    """
    users = get_all_users()
    if users:
        return jsonify(users)
    else:
        return jsonify({'error': 'Failed to fetch users from Azure DevOps'}), 500

@app.route('/api/automated_task_assignment/fetch_unassigned_tasks', methods=['GET'])
def fetch_tasks():
    """
    Flask route to fetch and return all unassigned tasks as JSON.
    """
    tasks = fetch_unassigned_tasks()
    if tasks:
        return jsonify(tasks)
    else:
        return jsonify({'error': 'Failed to fetch unassigned tasks from Azure DevOps'}), 500

@app.route('/api/automated_task_assignment/task_counts', methods=['GET'])
def fetch_task_counts():
    """
    Flask route to fetch the count of tasks assigned to each user.
    """
    task_counts = get_work_item_counts_for_all_users()
    if task_counts:
        return jsonify(task_counts)
    else:
        return jsonify({'error': 'Failed to fetch task counts for users'}), 500

@app.route('/api/automated_task_assignment/update_work_item/<int:work_item_id>/<user_email>', methods=['POST'])
def update_work_item(work_item_id, user_email):
    """
    Flask route to update the 'Assigned To' field of a work item.
    """
    if not work_item_id or not user_email:
        return jsonify({'error': 'Missing work_item_id or user_email'}), 400

    result = update_work_item_assigned_to(work_item_id, user_email)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to update work item'}), 500
    
@app.route('/api/status_report/generate_gpt_task_assignment/<task_id>', methods=['POST'])
def generate_gpt_task_assignment_route(task_id):
    """
    Flask route to generate task assignments using GPT.
    """
    if not task_id:
        return jsonify({'error': 'Missing task_id parameter'}), 400
    
    try:
        assignments = generate_gpt_task_assignment(task_id, fetch_all_work_items())
        return jsonify(assignments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status_report/fetch_pending_tasks/<due_date>', methods=['POST'])
def fetch_pending_tasks_route(due_date):
    if not due_date:
        return jsonify({'error': 'Missing due_date parameter'}), 400

    tasks = fetch_pending_tasks(due_date)
    if tasks:
        return jsonify(tasks)
    else:
        return jsonify({'error': 'Failed to fetch pending tasks'}), 500

@app.route('/api/stats/count_work_items_by_state', methods=['GET'])
def count_work_items_by_state_route():


    counts = count_work_items_by_state()
    if counts:
        return jsonify(counts)
    else:
        return jsonify({'error': 'Failed to count work items by state'}), 500
    
@app.route('/api/stats/count_work_items_by_assignment', methods=['GET'])
def count_work_items_by_assignment_route():
    counts = count_work_items_by_assignment()
    if counts:
        return jsonify(counts)
    else:
        return jsonify({'error': 'Failed to count work items by assignment'}), 500
    
@app.route('/api/stats/count_work_items_by_type', methods=['GET'])
def count_work_items_by_type_route():
    counts = count_work_items_by_type()
    if counts:
        return jsonify(counts)
    else:
        return jsonify({'error': 'Failed to count work items by assignment'}), 500

@app.route('/api/receive-token', methods=['POST'])
def receive_token():
    if request.content_type != 'application/json':
        return jsonify({'error': 'Content-Type must be application/json'}), 415

    data = request.get_json()
    jwt_token = data.get('access_token')
    set_jwt_token(jwt_token)
    if get_jwt_token():
        print(f"Received token: {get_jwt_token()}")
        return jsonify({"message": "Token received successfully", "status": "success"}), 200
    else:
        return jsonify({"message": "No token provided", "status": "error"}), 400



@app.route('/api/automated_task_assignment/bulk_update', methods=['POST'])
def bulk_update():
    data = request.json  # Expecting a list of { taskId: email } pairs
    results = []
    
    for task in data:
        task_id = task.get('taskId')
        email = task.get('email')
        
        result = update_work_item_assigned_to(task_id, email)
        
        #success = True  # Assume success for demonstration

        if result:
            results.append({task_id: "Assigned"})
        else:
            results.append({task_id: "Failed"})
    
    return jsonify(results), 200

@app.route('/api/status_report/generate_gpt_task_assignment', methods=['POST'])
def generate_gpt_task_assignment_route_all():
    """
    Flask route to generate task assignments using GPT for single or multiple task IDs.
    """
    data = request.get_json()
    
   
    task_ids = data.get('task_id') or data.get('task_ids')
    if not task_ids:
        return jsonify({'error': 'Missing task_id or task_ids parameter'}), 400

    if isinstance(task_ids, str):
        task_ids = [task_ids]

    try:
        assignments = []
        for task_id in task_ids:
            task_assignment = generate_gpt_task_assignment(task_id, fetch_all_work_items())
            assignments.append({task_id: task_assignment})
        
        return jsonify(assignments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk/filter_risk_items', methods=['GET'])
def fetch_filter_risks():
    """
    Flask route to filter risk items.
    """
    try:
        risk_items = filter_risk_items()
        if not risk_items:
            return jsonify({'items': [], 'error': 'No risk data returned'}), 200

        if isinstance(risk_items, str):
            try:
                risk_items = json.loads(risk_items)
            except json.JSONDecodeError:
                return (
                    jsonify(
                        {
                            'items': [],
                            'error': 'Invalid JSON from risk model',
                        }
                    ),
                    500,
                )

        if isinstance(risk_items, dict):
            return jsonify(risk_items)

        return jsonify({'items': [], 'error': 'Unexpected response type'}), 500
    except Exception as e:
        return jsonify({'items': [], 'error': str(e)}), 500

@app.route('/api/email_sender/create_draft', methods=['POST'])
def create_draft():
    """
    API Endpoint to create a draft email using Microsoft Graph API.
    """
    data = request.get_json()
    subject = data.get('subject')
    body = data.get('body')
    to_recipients = data.get('to_recipients')
    attachments = data.get('attachments', None)

    if not subject or not body or not to_recipients:
        return jsonify({'error': 'Missing subject, body, or to_recipients parameter'}), 400

    # Assuming you fetch an access token for authentication
    #access_token = jwt_token  # You need to implement this function to fetch a valid token
    try:
        # Instantiate the email sender
        email_sender = OutlookEmailSender(get_jwt_token())

        # Use the OutlookEmailSender's send_email method to create a draft
        draft_link = email_sender.send_mail(subject, body, to_recipients)

        return jsonify({
            'message': 'Draft created successfully',
            'draft_link': draft_link
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/email_sender/generate_email_ai', methods=['POST'])
def generate_email_ai():
    """
    API Endpoint to generate an email using GPT-4.
    """
    data = request.get_json()
    to = data.get('to')
    to_name = data.get('to_name')
    from_ = data.get('from')
    from_name = data.get('from_name')
    context = data.get('context')
    
    if not to or not from_ or not context:
        return jsonify({'error': 'Missing to, from, or context parameter'}), 400

    try:
        email = generate_gpt_email(to, to_name, from_, from_name, context)
        subject = generate_subject_line(context)
        return jsonify({'email': email, 'subject': subject})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/generate_status_report_plan', methods=['GET'])
def generate_status_report_plan_route():
    """
    Flask route to generate a status report plan and return the file.
    """
    status_report_plan = organize_tasks_by_due_date()
    if status_report_plan:
        file_path = status_report_plan
        if file_path and os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File path is invalid or file does not exist'}), 500
    else:
        return jsonify({'error': 'Failed to generate status report plan'}), 500

@app.route('/api/get_projects', methods=['GET'])
def get_projects_route():
    """
    Flask route to fetch and return all projects as JSON.
    """
    projects = fetch_user_projects()
    if projects:
        return jsonify(projects)
    else:
        return jsonify({'error': 'Failed to fetch projects from Azure DevOps'}), 500

@app.route('/api/get_current_project', methods=['GET'])
def fetch_current_projects():
    """
    Flask route to fetch and return all projects as JSON.
    """
    projects = get_current_project()
    if projects:
        return jsonify(projects)
    else:
        return jsonify({'error': 'Failed to fetch current project from Azure DevOps'}), 500

# @app.route('/api/switch_project', methods=['POST'])
# def switch_project():
#     """
#     Flask route to switch the current project.
#     """
    
#     data = request.get_json()
#     new_project_name = data.get('project')

#     if new_project_name:
#         # Update the global variable
#         os.environ['PROJECT_NAME'] = new_project_name
#         #PROJECT_NAME = new_project_name
#         print(f"Switched to project: {PROJECT_NAME}")
#         return jsonify({'message': f'Switched to project: {PROJECT_NAME}'}), 200
#     else:
#         return jsonify({'error': 'Invalid project name provided'}), 400
@app.route('/api/switch_project', methods=['POST'])
def switch_project():
    """
    Flask route to switch the current project.
    """
    data = request.get_json()
    new_project_name = data.get('project')
    if new_project_name:
        # Update the .env file with the new project name
        set_project_name(new_project_name)
        #print(f"Switched to project: {new_project_name}")
        print(f"Switched to project: {get_project_name()}")
        return jsonify({'message': f'Switched to project: {new_project_name}'}), 200
    else:
        return jsonify({'error': 'Invalid project name provided'}), 400


@app.route('/api/chatbot/send_message', methods=['POST'])
def send_message_to_chatbot():
    """
    Route to send a message to the chatbot and receive its response.
    """
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'Message content is required'}), 400

    try:
        response = chat_handler.handle_message(user_message)
        
        # Filter out responses without content or with role 'tool'
        filtered_response = [
            msg for msg in response['messages']
            if msg.get('content') and msg.get('role') != 'tool' and msg.get('role') != 'system'
        ]

        return jsonify({'messages': filtered_response})
    except Exception as e:
        # Always return `messages` so the UI does not crash on optional chaining
        return jsonify({'messages': [], 'error': str(e)}), 500


@app.route('/api/chatbot/chat_history', methods=['GET'])
def get_chat_history():
    """
    Route to retrieve the chat history.
    """
    try:
        chat_history = chat_handler.get_chat_history()
        return jsonify({'chat_history': chat_history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chatbot/reset_chat', methods=['POST'])
def reset_chat_history():
    """
    Route to reset the chat history.
    """
    try:
        chat_handler.chat_data.reset()
        return jsonify({'message': 'Chat history reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-report')
def download_report():
    file_path = r'C:\Users\ppatel08\ITCaseComp\FGF-ItCaseComp\Back End\work_items_due_dates.xlsx'  # Path to your file
    return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)

