import requests
from requests.auth import HTTPBasicAuth
from app.config import PAT, get_project_name, get_azure_devops_rest_api_url
import logging


def count_work_items_by_state():
    """
    Count work items from Azure DevOps grouped by their state without filtering by due date.
    
    Returns:
        Optional[Dict[str, int]]: A dictionary with states as keys and their counts as values, or None on failure.
    """
    url = f'{get_azure_devops_rest_api_url()}/wit/wiql?api-version=7.1-preview.2'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password

    query = {
        "query": f"""
        SELECT [System.Id], [System.State]
        FROM WorkItems
        WHERE [System.TeamProject] = '{get_project_name()}'
        ORDER BY [System.ChangedDate] DESC
        """
    }
    print(get_project_name())
    try:
        response = requests.post(url, auth=auth, json=query)
        if response.status_code != 200:
            logging.error(f'Failed to execute WIQL query: {response.status_code}')
            return None

        work_item_refs = response.json().get('workItems', [])
        work_item_ids = [item['id'] for item in work_item_refs]

        if not work_item_ids:
            logging.info("No work items found.")
            return {}

        # Fetch details in batches
        state_counts = {}
        for i in range(0, len(work_item_ids), 200):
            batch_ids = work_item_ids[i:i+200]
            details_url = f"{get_azure_devops_rest_api_url()}/wit/workitemsbatch?api-version=7.1-preview.1"
            details_payload = {"ids": batch_ids}

            details_response = requests.post(details_url, auth=auth, json=details_payload)
            if details_response.status_code != 200:
                logging.error(f'Failed to fetch work item details: {details_response.status_code}')
                return None

            for work_item in details_response.json().get('value', []):
                state = work_item.get('fields', {}).get('System.State', 'Unknown')
                state_counts[state] = state_counts.get(state, 0) + 1

        return state_counts
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed: {e}')
        return None

def count_work_items_by_assignment():
    """
    Count work items from Azure DevOps grouped by assigned vs unassigned.
    
    Returns:
        Optional[Dict[str, int]]: A dictionary with assigned,unassigned as keys and their counts as values, or None on failure.
    """
    url = f'{get_azure_devops_rest_api_url()}/wit/wiql?api-version=7.1-preview.2'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password

    query = {
        "query": f"""
        SELECT [System.Id], [System.State]
        FROM WorkItems
        WHERE [System.TeamProject] = '{get_project_name()}'
        ORDER BY [System.ChangedDate] DESC
        """
    }
    print(get_project_name())
    try:
        response = requests.post(url, auth=auth, json=query)
        if response.status_code != 200:
            logging.error(f'Failed to execute WIQL query: {response.status_code}')
            return None

        work_item_refs = response.json().get('workItems', [])
        work_item_ids = [item['id'] for item in work_item_refs]

        if not work_item_ids:
            logging.info("No work items found.")
            return {}

        # Fetch details in batches
        assignment_counts = {'assigned': 0, 'unassigned': 0}
        for i in range(0, len(work_item_ids), 200):
            batch_ids = work_item_ids[i:i+200]
            details_url = f"{get_azure_devops_rest_api_url()}/wit/workitemsbatch?api-version=7.1-preview.1"
            details_payload = {"ids": batch_ids}

            details_response = requests.post(details_url, auth=auth, json=details_payload)
            if details_response.status_code != 200:
                logging.error(f'Failed to fetch work item details: {details_response.status_code}')
                return None

            for work_item in details_response.json().get('value', []):
                assigned_to = work_item.get('fields', {}).get('System.AssignedTo')
                if assigned_to:
                    assignment_counts['assigned'] += 1
                else:
                    assignment_counts['unassigned'] += 1

        return assignment_counts
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed: {e}')
        return None

def count_work_items_by_type():
    """
    Count work items from Azure DevOps grouped by their state without filtering by due date.
    
    Returns:
        Optional[Dict[str, int]]: A dictionary with states as keys and their counts as values, or None on failure.
    """
    url = f'{get_azure_devops_rest_api_url()}/wit/wiql?api-version=7.1-preview.2'
    auth = HTTPBasicAuth('', PAT)  # Empty username, PAT as the password

    query = {
        "query": f"""
        SELECT [System.Id], [System.WorkItemType]
        FROM WorkItems
        WHERE [System.TeamProject] = '{get_project_name()}'
        ORDER BY [System.ChangedDate] DESC
        """
    }

    try:
        response = requests.post(url, auth=auth, json=query)
        if response.status_code != 200:
            logging.error(f'Failed to execute WIQL query: {response.status_code}')
            return None

        work_item_refs = response.json().get('workItems', [])
        work_item_ids = [item['id'] for item in work_item_refs]

        if not work_item_ids:
            logging.info("No work items found.")
            return {}

        # Fetch details in batches
        state_counts = {}
        for i in range(0, len(work_item_ids), 200):
            batch_ids = work_item_ids[i:i+200]
            details_url = f"{get_azure_devops_rest_api_url()}/wit/workitemsbatch?api-version=7.1-preview.1"
            details_payload = {"ids": batch_ids}

            details_response = requests.post(details_url, auth=auth, json=details_payload)
            if details_response.status_code != 200:
                logging.error(f'Failed to fetch work item details: {details_response.status_code}')
                return None

            for work_item in details_response.json().get('value', []):
                state = work_item.get('fields', {}).get('System.WorkItemType', 'Unknown')
                state_counts[state] = state_counts.get(state, 0) + 1

        return state_counts
    except requests.exceptions.RequestException as e:
        logging.error(f'Request failed: {e}')
        return None