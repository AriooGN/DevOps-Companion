import requests
import logging
from requests.auth import HTTPBasicAuth
from app.config import get_azure_devops_rest_api_url, PAT, get_project_name
import pandas as pd
from datetime import datetime

def fetch_all_work_items():
    """
    Fetch all work items from Azure DevOps for a given project.
    
    Parameters:
        azure_devops_url (str): Base URL for Azure DevOps REST API.
        project_name (str): Name of the Azure DevOps project.
        pat (str): Personal Access Token for authentication.
    
    Returns:
        dict: A dictionary with work items, or None if an error occurred.
    """
    url = f'{get_azure_devops_rest_api_url()}/wit/wiql?api-version=7.1-preview.2'
    
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password

    # Define the WIQL query
    query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.TeamProject], [Microsoft.VSTS.Common.Priority], [Microsoft.VSTS.Common.Severity], [Microsoft.VSTS.Scheduling.DueDate]
        FROM WorkItems
        WHERE [System.TeamProject] = '{get_project_name()}'
        ORDER BY [System.ChangedDate] DESC
        """
    }


    try:
        logging.debug(f'WIQL Query URL: {url}')
        logging.debug(f'WIQL Query Payload: {query}')

        # Send POST request to execute the WIQL query
        response = requests.post(url, auth=auth, json=query)
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
                details_url = f"{get_azure_devops_rest_api_url()}/wit/workitemsbatch?api-version=7.1-preview.1"
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
            
            # Clean up the data
            cleaned_work_items = [
                {
                    "id": item.get("id"),
                    "title": item.get("fields", {}).get("System.Title", ""),
                    "state": item.get("fields", {}).get("System.State", ""),
                    "assigned_to": item.get("fields", {}).get("System.AssignedTo", {}).get("displayName", ""),
                    "team_project": item.get("fields", {}).get("System.TeamProject", ""),
                    "priority": item.get("fields", {}).get("Microsoft.VSTS.Common.Priority", ""),
                    "severity": item.get("fields", {}).get("Microsoft.VSTS.Common.Severity", ""),
                    "due_date": item.get("fields", {}).get("Microsoft.VSTS.Scheduling.DueDate", "")
                }
                for item in all_work_items
            ]
            return {"workItems": cleaned_work_items}
        else:
            logging.error(f'Failed to execute WIQL query: {response.status_code}')
            logging.error(f'Response Content: {response.content.decode()}')
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed: {e}')
        return None

def generate_ms_project_plan(work_items):
    """
    Generate an MS Project plan from work items.
    
    Parameters:
        work_items (list): List of work items.
    
    Returns:
        MSPProject: An MS Project plan object.
    """
    project = MSPProject()
    for item in work_items:
        task = MSPTask(
            id=item['id'],
            name=item['title'],
            start=datetime.strptime(item['due_date'], '%Y-%m-%dT%H:%M:%S.%fZ') if item['due_date'] else None,
            finish=datetime.strptime(item['due_date'], '%Y-%m-%dT%H:%M:%S.%fZ') if item['due_date'] else None,
            priority=item['priority'],
            resource_names=item['assigned_to']
        )
        project.add_task(task)
    return project

