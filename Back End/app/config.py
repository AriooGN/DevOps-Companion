import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_ROOT / ".env")

ORG_NAME = os.getenv("AZURE_DEVOPS_ORG", "").strip()
PROJECT_NAME = os.getenv("AZURE_DEVOPS_PROJECT", "").strip()
PAT = os.getenv("AZURE_DEVOPS_PAT", "").strip()
jwt_token = os.getenv("AZURE_DEVOPS_JWT_TOKEN", "").strip()

if not ORG_NAME or not PROJECT_NAME or not PAT:
    warnings.warn(
        "Set AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, and AZURE_DEVOPS_PAT in Back End/.env "
        "(see .env.example).",
        stacklevel=1,
    )


def _sync_api_urls():
    global AZURE_DEVOPS_GRAPH_API_URL, AZURE_DEVOPS_REST_API_URL
    AZURE_DEVOPS_GRAPH_API_URL = f"https://vssps.dev.azure.com/{ORG_NAME}/_apis/graph"
    AZURE_DEVOPS_REST_API_URL = (
        f"https://dev.azure.com/{ORG_NAME}/{PROJECT_NAME}/_apis"
    )


AZURE_DEVOPS_GRAPH_API_URL = ""
AZURE_DEVOPS_REST_API_URL = ""
_sync_api_urls()


def get_org_name():
    return ORG_NAME


def get_project_name():
    return PROJECT_NAME


def get_pat():
    return PAT


def get_jwt_token():
    return jwt_token


def get_azure_devops_graph_api_url():
    return AZURE_DEVOPS_GRAPH_API_URL


def get_azure_devops_rest_api_url():
    return AZURE_DEVOPS_REST_API_URL


def set_org_name(value):
    global ORG_NAME
    ORG_NAME = value
    _sync_api_urls()


def set_project_name(value):
    global PROJECT_NAME
    PROJECT_NAME = value
    _sync_api_urls()
    print(AZURE_DEVOPS_REST_API_URL)
    print(PROJECT_NAME,)


def set_pat(value):
    global PAT
    PAT = value


def set_jwt_token(value):
    global jwt_token
    jwt_token = value
