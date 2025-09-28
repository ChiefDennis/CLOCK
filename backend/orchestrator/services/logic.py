# /orchestrator/services/logic.py

import requests
from flask import jsonify
from models import ModuleStatus

# Define the endpoint URLs for each cloud module
CLOUD_MODULES = {
    "aws": "http://aws_module:5000",
    "azure": "http://azure_module:5000",
    "gcp": "http://gcp_module:5000"
}

def forward_request(endpoint, data, method="POST"):
    """
    Forwards a validated request to the appropriate cloud module.

    Args:
        endpoint (str): The specific action to trigger (e.g., 'get-key').
        data (dict): Validated payload from the client.
        method (str): The HTTP method to use ('GET' or 'POST').

    Returns:
        Tuple[dict, int]: A tuple containing the JSON response and status code.
    """
    cloud = data.get("cloud_provider")

    if not cloud or cloud not in CLOUD_MODULES:
        return {"error": "Invalid or missing cloud provider"}, 400

    # Check the module's status in the database.
    module_status = ModuleStatus.query.filter_by(provider_name=cloud).first()
    if not module_status or not module_status.is_enabled:
        return {"error": f"The '{cloud}' module is currently disabled by an administrator."}, 503 # 503 Service Unavailable is appropriate

    url = f"{CLOUD_MODULES[cloud]}/{endpoint}"

    try:
        response = None
        if method.upper() == "GET":
            # For GET requests, data is sent as query parameters using 'params'
            response = requests.get(url, params=data, timeout=10)
        elif method.upper() == "POST":
            # For POST requests, data is sent as a JSON body
            response = requests.post(url, json=data, timeout=10)
        else:
            return {"error": f"Unsupported internal method: {method}"}, 500
        
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        
        return response.json(), response.status_code

    except requests.exceptions.HTTPError as e:
        # Return the actual error from the downstream service if possible
        error_json = e.response.json() if e.response.content else {"error": e.response.reason}
        return error_json, e.response.status_code
        
    except requests.exceptions.RequestException as e:
        # Handle network/service-level errors (e.g., timeout, connection error)
        return {
            "error": "Module unavailable or network error",
            "details": str(e)
        }, 503