"""Airtable MCP Server with FastMCP and Structured Output"""

import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv(override=True)

# Initialize FastMCP server
mcp = FastMCP("Airtable API Server")

# Configuration
AIRTABLE_API_BASE = "https://api.airtable.com/v0"

# Nango authentication
def get_connection_credentials() -> Dict[str, Any]:
    """Get credentials from Nango"""
    connection_id = os.environ.get("NANGO_CONNECTION_ID")
    integration_id = os.environ.get("NANGO_INTEGRATION_ID")
    base_url = os.environ.get("NANGO_BASE_URL")
    secret_key = os.environ.get("NANGO_SECRET_KEY")
    
    if not all([connection_id, integration_id, base_url, secret_key]):
        missing_vars = [
            var for var, val in [
                ("NANGO_CONNECTION_ID", connection_id),
                ("NANGO_INTEGRATION_ID", integration_id),
                ("NANGO_BASE_URL", base_url),
                ("NANGO_SECRET_KEY", secret_key)
            ] if not val
        ]
        raise ValueError(f"Missing required Nango environment variables: {', '.join(missing_vars)}")
    
    url = f"{base_url}/connection/{connection_id}"
    params = {
        "provider_config_key": integration_id,
        "refresh_token": "true",
    }
    headers = {"Authorization": f"Bearer {secret_key}"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to get Nango credentials: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Nango response: {str(e)}")

def get_airtable_token() -> str:
    """Get Airtable token from Nango"""
    try:
        credentials = get_connection_credentials()
        # Extract access token from Nango response
        if "credentials" in credentials and "access_token" in credentials["credentials"]:
            return credentials["credentials"]["access_token"]
        elif "access_token" in credentials:
            return credentials["access_token"]
        else:
            raise ValueError("No access_token found in Nango credentials response")
    except Exception as e:
        raise ValueError(f"Failed to get authentication token from Nango: {str(e)}")

# Common headers for all requests
def get_headers() -> Dict[str, str]:
    """Get common headers for Airtable API requests"""
    token = get_airtable_token()
    
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

# Error handling wrapper
def handle_api_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Handle API requests with proper error handling"""
    try:
        headers = get_headers()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        
        # Handle empty responses
        if not response.content:
            return {"success": True}
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"raw_response": response.text}
    
    except requests.exceptions.HTTPError as e:
        error_detail = f"HTTP {e.response.status_code}: {e.response.reason}"
        try:
            error_body = e.response.json()
            error_detail += f" - {error_body.get('error', {}).get('message', str(error_body))}"
        except:
            error_detail += f" - {e.response.text}"
        raise ValueError(error_detail)
    
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Request failed: {str(e)}")
    
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")

# Base Models for structured output
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None

class Record(BaseModel):
    """Airtable record structure"""
    id: str
    createdTime: str
    fields: Dict[str, Any]
    commentCount: Optional[int] = None

class Field(BaseModel):
    """Airtable field structure"""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class Table(BaseModel):
    """Airtable table structure"""
    id: str
    name: str
    description: Optional[str] = None
    primaryFieldId: str
    fields: List[Field]

class Base(BaseModel):
    """Airtable base structure"""
    id: str
    name: str
    permissionLevel: str

class View(BaseModel):
    """Airtable view structure"""
    id: str
    name: str
    type: str
    personalForUserId: Optional[str] = None
    visibleFieldIds: Optional[List[str]] = None

class Comment(BaseModel):
    """Airtable comment structure"""
    id: str
    text: str
    createdTime: str
    lastUpdatedTime: Optional[str] = None
    author: Dict[str, Any]

class User(BaseModel):
    """Airtable user structure"""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None

class Webhook(BaseModel):
    """Airtable webhook structure"""
    id: str
    notificationUrl: Optional[str] = None
    isHookEnabled: bool
    areNotificationsEnabled: bool
    cursorForNextPayload: int
    lastSuccessfulNotificationTime: Optional[str] = None

class Enterprise(BaseModel):
    """Airtable enterprise structure"""
    id: str
    createdTime: str
    rootEnterpriseAccountId: str
    userIds: List[str]
    groupIds: List[str]
    workspaceIds: List[str]

@mcp.tool()
def list_records(
    base_id: str,
    table_id_or_name: str,
    fields: Optional[List[str]] = None,
    filter_by_formula: Optional[str] = None,
    max_records: Optional[int] = None,
    page_size: Optional[int] = None,
    sort: Optional[List[Dict[str, str]]] = None,
    view: Optional[str] = None,
    cell_format: Optional[str] = None,
    time_zone: Optional[str] = None,
    user_locale: Optional[str] = None
) -> Dict[str, Any]:
    """List records in a table"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}"
    params = {}
    
    if fields:
        for field in fields:
            params[f"fields[]"] = field
    if filter_by_formula:
        params["filterByFormula"] = filter_by_formula
    if max_records:
        params["maxRecords"] = max_records
    if page_size:
        params["pageSize"] = page_size
    if view:
        params["view"] = view
    if cell_format:
        params["cellFormat"] = cell_format
    if time_zone:
        params["timeZone"] = time_zone
    if user_locale:
        params["userLocale"] = user_locale
    if sort:
        for i, sort_obj in enumerate(sort):
            for key, value in sort_obj.items():
                params[f"sort[{i}][{key}]"] = value
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def get_record(
    base_id: str,
    table_id_or_name: str,
    record_id: str,
    cell_format: Optional[str] = None,
    return_fields_by_field_id: Optional[bool] = None
) -> Dict[str, Any]:
    """Retrieve a single record"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}/{record_id}"
    params = {}
    
    if cell_format:
        params["cellFormat"] = cell_format
    if return_fields_by_field_id is not None:
        params["returnFieldsByFieldId"] = return_fields_by_field_id
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def create_records(
    base_id: str,
    table_id_or_name: str,
    records: Optional[List[Dict[str, Any]]] = None,
    fields: Optional[Dict[str, Any]] = None,
    typecast: Optional[bool] = None,
    return_fields_by_field_id: Optional[bool] = None
) -> Dict[str, Any]:
    """Create one or more records"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}"
    data = {}
    
    if records:
        data["records"] = records
    elif fields:
        data["fields"] = fields
    
    if typecast is not None:
        data["typecast"] = typecast
    if return_fields_by_field_id is not None:
        data["returnFieldsByFieldId"] = return_fields_by_field_id
    
    return handle_api_request("POST", url, json=data)

@mcp.tool()
def update_record(
    base_id: str,
    table_id_or_name: str,
    record_id: str,
    fields: Dict[str, Any],
    typecast: Optional[bool] = None,
    return_fields_by_field_id: Optional[bool] = None
) -> Dict[str, Any]:
    """Update a single record"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}/{record_id}"
    data = {"fields": fields}
    
    if typecast is not None:
        data["typecast"] = typecast
    if return_fields_by_field_id is not None:
        data["returnFieldsByFieldId"] = return_fields_by_field_id
    
    return handle_api_request("PATCH", url, json=data)

@mcp.tool()
def update_multiple_records(
    base_id: str,
    table_id_or_name: str,
    records: List[Dict[str, Any]],
    typecast: Optional[bool] = None,
    return_fields_by_field_id: Optional[bool] = None,
    perform_upsert: Optional[bool] = None,
    fields_to_merge_on: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Update multiple records"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}"
    data = {"records": records}
    
    if typecast is not None:
        data["typecast"] = typecast
    if return_fields_by_field_id is not None:
        data["returnFieldsByFieldId"] = return_fields_by_field_id
    if perform_upsert is not None:
        data["performUpsert"] = perform_upsert
    if fields_to_merge_on:
        data["fieldsToMergeOn"] = fields_to_merge_on
    
    return handle_api_request("PATCH", url, json=data)

@mcp.tool()
def delete_record(
    base_id: str,
    table_id_or_name: str,
    record_id: str
) -> Dict[str, Any]:
    """Delete a single record"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}/{record_id}"
    return handle_api_request("DELETE", url)

@mcp.tool()
def delete_multiple_records(
    base_id: str,
    table_id_or_name: str,
    record_ids: List[str]
) -> Dict[str, Any]:
    """Delete multiple records"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}"
    params = {"records[]": record_ids}
    return handle_api_request("DELETE", url, params=params)

# Bases API Tools
@mcp.tool()
def list_bases(offset: Optional[str] = None) -> Dict[str, Any]:
    """List all accessible bases"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases"
    params = {}
    if offset:
        params["offset"] = offset
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def get_base_schema(base_id: str, include: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get base schema including tables and fields"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/tables"
    params = {}
    if include:
        params["include"] = include
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def create_base(
    name: str,
    workspace_id: str,
    tables: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create a new base"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases"
    data = {
        "name": name,
        "workspaceId": workspace_id,
        "tables": tables
    }
    
    return handle_api_request("POST", url, json=data)

@mcp.tool()
def get_base_collaborators(
    base_id: str,
    include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get base collaborators and permissions"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}"
    params = {}
    if include:
        params["include"] = include
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def delete_base(base_id: str) -> Dict[str, Any]:
    """Delete a base"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}"
    return handle_api_request("DELETE", url)

# Tables API Tools
@mcp.tool()
def create_table(
    base_id: str,
    name: str,
    fields: List[Dict[str, Any]],
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new table"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/tables"
    data = {
        "name": name,
        "fields": fields
    }
    if description:
        data["description"] = description
    
    return handle_api_request("POST", url, json=data)

@mcp.tool()
def update_table(
    base_id: str,
    table_id_or_name: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Update table metadata"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/tables/{table_id_or_name}"
    data = {}
    
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    
    return handle_api_request("PATCH", url, json=data)

# Fields API Tools
@mcp.tool()
def create_field(
    base_id: str,
    table_id: str,
    name: str,
    type: str,
    description: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new field"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/tables/{table_id}/fields"
    data = {
        "name": name,
        "type": type
    }
    
    if description is not None:
        data["description"] = description
    if options is not None:
        data["options"] = options
    
    return handle_api_request("POST", url, json=data)

@mcp.tool()
def update_field(
    base_id: str,
    table_id: str,
    field_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Update field metadata"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/tables/{table_id}/fields/{field_id}"
    data = {}
    
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    
    return handle_api_request("PATCH", url, json=data)

# Views API Tools
@mcp.tool()
def list_views(base_id: str, include: Optional[List[str]] = None) -> Dict[str, Any]:
    """List all views in a base"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/views"
    params = {}
    if include:
        params["include"] = include
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def get_view_metadata(
    base_id: str,
    view_id: str,
    include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get view metadata"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/views/{view_id}"
    params = {}
    if include:
        params["include"] = include
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def delete_view(base_id: str, view_id: str) -> Dict[str, Any]:
    """Delete a view"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/views/{view_id}"
    return handle_api_request("DELETE", url)

# Comments API Tools
@mcp.tool()
def list_comments(
    base_id: str,
    table_id_or_name: str,
    record_id: str,
    page_size: Optional[int] = None,
    offset: Optional[str] = None
) -> Dict[str, Any]:
    """List comments on a record"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}/{record_id}/comments"
    params = {}
    
    if page_size is not None:
        params["pageSize"] = page_size
    if offset:
        params["offset"] = offset
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def create_comment(
    base_id: str,
    table_id_or_name: str,
    record_id: str,
    text: str,
    parent_comment_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a comment on a record"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}/{record_id}/comments"
    data = {"text": text}
    
    if parent_comment_id:
        data["parentCommentId"] = parent_comment_id
    
    return handle_api_request("POST", url, json=data)

@mcp.tool()
def update_comment(
    base_id: str,
    table_id_or_name: str,
    record_id: str,
    comment_id: str,
    text: str
) -> Dict[str, Any]:
    """Update a comment"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}/{record_id}/comments/{comment_id}"
    data = {"text": text}
    
    return handle_api_request("PATCH", url, json=data)

@mcp.tool()
def delete_comment(
    base_id: str,
    table_id_or_name: str,
    record_id: str,
    comment_id: str
) -> Dict[str, Any]:
    """Delete a comment"""
    
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_id_or_name}/{record_id}/comments/{comment_id}"
    return handle_api_request("DELETE", url)

# Webhooks API Tools
@mcp.tool()
def list_webhooks(base_id: str) -> Dict[str, Any]:
    """List all webhooks for a base"""
    
    url = f"{AIRTABLE_API_BASE}/bases/{base_id}/webhooks"
    return handle_api_request("GET", url)

@mcp.tool()
def create_webhook(
    base_id: str,
    notification_url: Optional[str] = None,
    specification: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a webhook"""
    
    url = f"{AIRTABLE_API_BASE}/bases/{base_id}/webhooks"
    data = {}
    
    if notification_url:
        data["notificationUrl"] = notification_url
    if specification:
        data["specification"] = specification
    
    return handle_api_request("POST", url, json=data)

@mcp.tool()
def delete_webhook(base_id: str, webhook_id: str) -> Dict[str, Any]:
    """Delete a webhook"""
    
    url = f"{AIRTABLE_API_BASE}/bases/{base_id}/webhooks/{webhook_id}"
    return handle_api_request("DELETE", url)

@mcp.tool()
def list_webhook_payloads(
    base_id: str,
    webhook_id: str,
    cursor: Optional[int] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """List webhook payloads"""
    
    url = f"{AIRTABLE_API_BASE}/bases/{base_id}/webhooks/{webhook_id}/payloads"
    params = {}
    
    if cursor is not None:
        params["cursor"] = cursor
    if limit is not None:
        params["limit"] = limit
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def enable_disable_webhook_notifications(
    base_id: str,
    webhook_id: str,
    enable: bool
) -> Dict[str, Any]:
    """Enable or disable webhook notifications"""
    
    url = f"{AIRTABLE_API_BASE}/bases/{base_id}/webhooks/{webhook_id}/enableNotifications"
    data = {"enable": enable}
    
    return handle_api_request("POST", url, json=data)

@mcp.tool()
def refresh_webhook(base_id: str, webhook_id: str) -> Dict[str, Any]:
    """Refresh a webhook to extend its life"""
    
    url = f"{AIRTABLE_API_BASE}/bases/{base_id}/webhooks/{webhook_id}/refresh"
    return handle_api_request("POST", url)

# Collaborators API Tools
@mcp.tool()
def add_base_collaborator(
    base_id: str,
    user_id: Optional[str] = None,
    group_id: Optional[str] = None,
    permission_level: str = "read"
) -> Dict[str, Any]:
    """Add a collaborator to a base"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/collaborators"
    
    collaborators = []
    if user_id:
        collaborators.append({
            "user": {"id": user_id},
            "permissionLevel": permission_level
        })
    elif group_id:
        collaborators.append({
            "group": {"id": group_id},
            "permissionLevel": permission_level
        })
    
    data = {"collaborators": collaborators}
    return handle_api_request("POST", url, json=data)

@mcp.tool()
def update_collaborator_base_permission(
    base_id: str,
    user_or_group_id: str,
    permission_level: str
) -> Dict[str, Any]:
    """Update collaborator permissions on a base"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/collaborators/{user_or_group_id}"
    data = {"permissionLevel": permission_level}
    
    return handle_api_request("PATCH", url, json=data)

@mcp.tool()
def delete_base_collaborator(base_id: str, user_or_group_id: str) -> Dict[str, Any]:
    """Remove a collaborator from a base"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/collaborators/{user_or_group_id}"
    return handle_api_request("DELETE", url)

@mcp.tool()
def get_workspace_collaborators(
    workspace_id: str,
    include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get workspace collaborators"""
    
    url = f"{AIRTABLE_API_BASE}/meta/workspaces/{workspace_id}"
    params = {}
    if include:
        params["include"] = include
    
    return handle_api_request("GET", url, params=params)

# User Info API Tools
@mcp.tool()
def get_user_info() -> Dict[str, Any]:
    """Get current user information"""
    
    url = f"{AIRTABLE_API_BASE}/meta/whoami"
    return handle_api_request("GET", url)

# Enterprise API Tools
@mcp.tool()
def get_enterprise(
    enterprise_account_id: str,
    include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get enterprise account information"""
    
    url = f"{AIRTABLE_API_BASE}/meta/enterpriseAccounts/{enterprise_account_id}"
    params = {}
    if include:
        params["include"] = include
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def get_user_by_id(
    enterprise_account_id: str,
    user_id: str,
    include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get user by ID in enterprise"""
    
    url = f"{AIRTABLE_API_BASE}/meta/enterpriseAccounts/{enterprise_account_id}/users/{user_id}"
    params = {}
    if include:
        params["include"] = include
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def get_users_by_id_or_email(
    enterprise_account_id: str,
    user_ids: Optional[List[str]] = None,
    emails: Optional[List[str]] = None,
    include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get users by ID or email"""
    
    url = f"{AIRTABLE_API_BASE}/meta/enterpriseAccounts/{enterprise_account_id}/users"
    params = {}
    
    if user_ids:
        for user_id in user_ids:
            params["id[]"] = user_id
    if emails:
        for email in emails:
            params["email[]"] = email
    if include:
        params["include"] = include
    
    return handle_api_request("GET", url, params=params)

@mcp.tool()
def remove_user_from_enterprise(
    enterprise_account_id: str,
    user_id: str,
    replacement_owner_id: Optional[str] = None,
    remove_from_descendants: Optional[bool] = None,
    is_dry_run: Optional[bool] = None
) -> Dict[str, Any]:
    """Remove user from enterprise"""
    
    url = f"{AIRTABLE_API_BASE}/meta/enterpriseAccounts/{enterprise_account_id}/users/{user_id}/remove"
    data = {}
    
    if replacement_owner_id:
        data["replacementOwnerId"] = replacement_owner_id
    if remove_from_descendants is not None:
        data["removeFromDescendants"] = remove_from_descendants
    if is_dry_run is not None:
        data["isDryRun"] = is_dry_run
    
    return handle_api_request("POST", url, json=data)

# Shares API Tools
@mcp.tool()
def list_shares(base_id: str) -> Dict[str, Any]:
    """List base shares"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/shares"
    return handle_api_request("GET", url)

@mcp.tool()
def delete_share(base_id: str, share_id: str) -> Dict[str, Any]:
    """Delete a share"""
    
    url = f"{AIRTABLE_API_BASE}/meta/bases/{base_id}/shares/{share_id}"
    return handle_api_request("DELETE", url)

def main():
    """Main function to run the MCP server"""
    mcp.run()
# Main entry point
if __name__ == "__main__": 
    main()