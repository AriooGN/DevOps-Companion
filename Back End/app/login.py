import requests
from app.config import AZURE_DEVOPS_REST_API_URL, PAT, ORG_NAME, get_project_name
import base64
def fetch_user_projects():
    """
    Fetch the list of projects a user is associated with in Azure DevOps.

    Args:
        auth_token (str): Personal Access Token (PAT) for Azure DevOps.

    Returns:
        list: A list of projects or None if the request fails.
    """
    API_VERSION = "7.1"  # Azure DevOps REST API version
    # Azure DevOps URL for organization-level projects
    url = f"https://dev.azure.com/{ORG_NAME}/_apis/projects?api-version={API_VERSION}"
    auth_header = base64.b64encode(f":{PAT}".encode()).decode()
    # Azure DevOps expects the Authorization header in Basic Auth format
    headers = {
        "Authorization": f"Basic {auth_header}",
    }

    try:
        # Make the API request
        response = requests.get(url, headers=headers)

        # Check for successful response
        if response.status_code == 200:
            # Return the project list as JSON
            return response.json().get("value", [])
        else:
            # Log error details and return None
            print(f"Error fetching projects: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_current_project():
    API_VERSION = "7.1"  # Azure DevOps REST API version
    # Azure DevOps URL for organization-level projects
    url = f"https://dev.azure.com/{ORG_NAME}/_apis/projects/{get_project_name()}?api-version={API_VERSION}"
    auth_header = base64.b64encode(f":{PAT}".encode()).decode()
    # Azure DevOps expects the Authorization header in Basic Auth format
    headers = {
        "Authorization": f"Basic {auth_header}",
    }
    try:
        # Make the API request
        response = requests.get(url, headers=headers)

        # Check for successful response
        if response.status_code == 200:
            # Return the project list as JSON
            return response.json()  
        else:
            # Log error details and return None
            print(f"Error fetching projects: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Example usage:
# auth_token = "EwCIA8l6BAAUbDba3x2OMJElkF7gJ4z/VbCPEz0AAdya5J2V7Ase6mMB/dOTccjHENxlP3EGGxFLrbWOnb3cbTX9hQKRLY0DJcJ2s5VzUZgAh57QhO+L27u/lR0FsuyIFlVTI3SGFmIhfb7a4oBcSPQBv0aaIhvq2rNio2qTUR3nFZOViK9q0cn51qOyTEgunDGROzxMwYd+3Q99Lc7bHMHFkdzJwAFHh8QfVNccUUGh/94glqrz1armC5MfxtGXisam9g/hfInepE/vu8HPs/Vh2oqea4aLS+zgVfujqUIe2lQG99XVWEChJCsA8GS3h35eTA+lhGcBzhO4XB5h6bnHIXCy0Ef4f5ujha53SztuT5Oj/ciCDzHar53TJCMQZgAAEJJcGXuIwMWxMpQMXhBvZ8xQAl65Wx2bZ6sEUsG/wkoo82T5hYwicaSxzdgtWmVlStwguDvRJ0HHYInM9kAXWotCTge2ei0DwnSkGmRU9FF3fzqktyrCA9IqU8BxXuBtGMeIRwoYGIaKxnxHG3lAP61hGSfMQA9TMi7CkxZBe+eARKzc6oGqAvr9E34/cp49kCYmXQhvz0ik/y8tn3+eCsw8QhOgwk87jVqltUGl1QWRroYhr/rX2j2PtJjx8GjKuVKL0q5ak6wmXhIcQ+sdeXWsSKlZVHXUdXkgqenzkKsTArLCLt6CptOhXpDJjRKiRYximXY6bvkv3x1qL5pvAIrtRtGyiec1yFS5qDI9AZJ3aKn0U3nDb3E1EjToN1r3ppdZDsmIFNQsq9f7bk1dQd3+9hwJKC1/kiwRhLCOlLOXsReg3eM38v//fSFxJbkkvvt4H1ajzrwWSsYhQHC1SorUG5jCNQVH/ui4neymgOUop6tB2T1GSGYBRGigeswaTIFY625E45F3xlXXWyz+8UdFdeZHmo/zPiWyXAvIdantpLVpterGCyFat2OOksS58RyVOA5SvGR7NczUfueSaryqbw5ajbFmOauLI1bFBbkmICSB4z2p7iwveDDe5PJjMLDwNwztSY/5fI76J2NiQdJHt6KxwnbpFoMLhGS0Vb4DKjsaDZtlum7FnEuu/zimY8lNDzIXuxhQ+i1Y9gPSEY8BA7KRwwfFFPdoIlV3TP8cvfwhkU46/FDz5YbNkoxkc7VRqM3tJEwB8LxY1le8esrRKHhHzqQrBJaJ/Pu+LCRE+72IAg=="
# projects = fetch_user_projects()
# print(projects)

def save_auth_token(auth_token, file_path):
    try:
        with open(file_path, 'w') as file:
            file.write(auth_token)
        print("Auth token saved successfully.")
    except Exception as e:
        print(f"An error occurred while saving the auth token: {e}")

