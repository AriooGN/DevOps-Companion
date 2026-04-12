import requests
from requests.auth import HTTPBasicAuth
from app.config import get_azure_devops_rest_api_url, PAT, get_org_name, get_project_name
import logging
import pandas as pd
from datetime import datetime, timedelta

def fetch_pending_tasks(due_date):
    """
    Fetch work items from Azure DevOps that are not marked as done and have a due date past the specified date.
    
    Args:
        due_date (str): The date in YYYY-MM-DD format to filter tasks with due dates past this value.
    
    Returns:
        dict or None: A dictionary of work items or None in case of failure.
    """
    url = f'https://dev.azure.com/{get_org_name()}/{get_project_name()}/_apis/wit/wiql?api-version=7.1-preview.2'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password
    due_date = datetime.today().strftime('%Y-%m-%d')

    # Define the WIQL query
    query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [Microsoft.VSTS.Scheduling.DueDate]
        FROM WorkItems
        WHERE [System.State] <> 'Done'
        AND [Microsoft.VSTS.Scheduling.DueDate] > '{due_date}'
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

def get_friday_dates():
    today = datetime.today()
    this_friday = today + timedelta((4 - today.weekday()) % 7)
    next_friday = this_friday + timedelta(7)
    friday_after_next = next_friday + timedelta(8)
    return this_friday, next_friday, friday_after_next

def fetch_all_pending_tasks(due_date):
    """
    Fetch all work items from Azure DevOps that are not marked as done and have a due date before the specified date.
    
    Args:
        due_date (str): The date in YYYY-MM-DD format to filter tasks with due dates before this value.
    
    Returns:
        list or None: A list of work items or None in case of failure.
    """
    url = f'https://dev.azure.com/{get_org_name()}/{get_project_name()}/_apis/wit/wiql?api-version=7.1-preview.2'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password

    # Define the WIQL query
    query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [Microsoft.VSTS.Scheduling.DueDate]
        FROM WorkItems
        WHERE [System.State] <> 'Done'
        AND [Microsoft.VSTS.Scheduling.DueDate] <= '{due_date}'
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
            
            return all_work_items
        else:
            logging.error(f'Failed to execute WIQL query: {response.status_code}')
            logging.error(f'Response Content: {response.content.decode()}')
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed: {e}')
        return None

def organize_tasks_by_due_date():
    this_friday, next_friday, friday_after_next = get_friday_dates()
    
    all_tasks = fetch_all_pending_tasks(friday_after_next.strftime('%Y-%m-%d'))
    
    if all_tasks is None:
        logging.error('Failed to fetch tasks')
        return
    
    tasks_this_friday = []
    tasks_next_friday = []
    tasks_friday_after_next = []
    
    for task in all_tasks:
        due_date = task['fields'].get('Microsoft.VSTS.Scheduling.DueDate')
        if due_date:
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M:%S.%fZ').date()
            except ValueError:
                due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M:%SZ').date()
            if due_date <= this_friday.date():
                tasks_this_friday.append(task)
            elif due_date <= next_friday.date():
                tasks_next_friday.append(task)
            else:
                tasks_friday_after_next.append(task)
    
    def extract_relevant_fields(tasks):
        extracted_tasks = []
        for task in tasks:
            fields = task['fields']
            extracted_tasks.append({
                'ID': task['id'],
                'Title': fields.get('System.Title', ''),
                'State': fields.get('System.State', ''),
                'Assigned To': fields.get('System.AssignedTo', {}).get('displayName', ''),
                'Due Date': fields.get('Microsoft.VSTS.Scheduling.DueDate', ''),
                'Created By': fields.get('System.CreatedBy', {}).get('displayName', ''),
                'Priority': fields.get('Microsoft.VSTS.Common.Priority', ''),
                'Severity': fields.get('Microsoft.VSTS.Common.Severity', '')
            })
        return extracted_tasks
    
    tasks_this_friday = extract_relevant_fields(tasks_this_friday)
    tasks_next_friday = extract_relevant_fields(tasks_next_friday)
    tasks_friday_after_next = extract_relevant_fields(tasks_friday_after_next)
    
    # Create DataFrames for each set of tasks
    df_this_friday = pd.DataFrame(tasks_this_friday)
    df_next_friday = pd.DataFrame(tasks_next_friday)
    df_friday_after_next = pd.DataFrame(tasks_friday_after_next)
    
    # Create an Excel writer object
    with pd.ExcelWriter('work_items_due_dates.xlsx', engine='xlsxwriter') as writer:
        df_this_friday.to_excel(writer, sheet_name='This Friday', index=False)
        df_next_friday.to_excel(writer, sheet_name='Next Friday', index=False)
        df_friday_after_next.to_excel(writer, sheet_name='Friday After Next', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook  = writer.book
        worksheet_this_friday = writer.sheets['This Friday']
        worksheet_next_friday = writer.sheets['Next Friday']
        worksheet_friday_after_next = writer.sheets['Friday After Next']
        
        # Define a format for the header cells
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#7AC143',  # Change this to your desired color
            'border': 1
        })
        
        # Apply the format to the header cells
        for col_num, value in enumerate(df_this_friday.columns.values):
            worksheet_this_friday.write(0, col_num, value, header_format)
        for col_num, value in enumerate(df_next_friday.columns.values):
            worksheet_next_friday.write(0, col_num, value, header_format)
        for col_num, value in enumerate(df_friday_after_next.columns.values):
            worksheet_friday_after_next.write(0, col_num, value, header_format)
    return "work_items_due_dates.xlsx"
