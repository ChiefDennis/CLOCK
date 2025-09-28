from functools import wraps
from flask import request, g
from werkzeug.exceptions import HTTPException
from models import Log
from extensions import db
import json

def log_request_response(action_name=None, hide_request_fields=None, hide_response_body=False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            
            # Helper function to redact sensitive data from a dictionary
            def _redact_data(data, fields_to_hide):
                if not fields_to_hide or not isinstance(data, dict):
                    return data
                
                # Make a copy to avoid modifying the original request data in-place
                redacted_data = data.copy()
                for field in fields_to_hide:
                    if field in redacted_data:
                        redacted_data[field] = "[REDACTED]"
                return redacted_data

            try:
                # --- SUCCESS PATH ---
                result = fn(*args, **kwargs)
                
                loggable_request_data = request.get_json(silent=True) or {}
                
                # Redact the request data before logging
                redacted_request_data = _redact_data(loggable_request_data, hide_request_fields)

                if isinstance(result, tuple):
                    response_obj, status_code = result[0], result[1]
                else:
                    response_obj, status_code = result, getattr(result, 'status_code', 200)

                response_data = ""
                if hide_response_body:
                    response_data = "[REDACTED]"
                elif hasattr(response_obj, 'get_data'):
                    response_data = response_obj.get_data(as_text=True)
                else:
                    response_data = json.dumps(response_obj)
                
                username_for_log = getattr(g, 'current_user', 'anonymous')
                if action_name == "User Login Attempt" and 'username' in loggable_request_data:
                    username_for_log = loggable_request_data['username']

                log = Log(
                    username=username_for_log,
                    role=getattr(g, 'current_role', 'none'),
                    method=request.method,
                    endpoint=request.path,
                    status_code=status_code,
                    # Use the redacted data for logging
                    request_data=json.dumps(redacted_request_data), # <<< CHANGED
                    response_data=response_data,
                    action=action_name
                )
                
                db.session.add(log)
                db.session.commit()
                
                return result

            except HTTPException as e:
                # --- FAILURE PATH (for HTTP errors like abort(401)) ---
                db.session.rollback()

                loggable_request_data = request.get_json(silent=True) or {}
                
                # Also redact data on failed requests
                redacted_request_data = _redact_data(loggable_request_data, hide_request_fields)

                username_for_log = 'anonymous'
                if action_name == "User Login Attempt" and 'username' in loggable_request_data:
                    username_for_log = loggable_request_data['username']

                log = Log(
                    username=username_for_log,
                    role=getattr(g, 'current_role', 'none'),
                    method=request.method,
                    endpoint=request.path,
                    status_code=e.code,
                    # Use the redacted data for logging
                    request_data=json.dumps(redacted_request_data), # <<< CHANGED
                    response_data=json.dumps(e.description),
                    action=f"Failed: {action_name}"
                )

                db.session.add(log)
                db.session.commit()
                raise e

            except Exception as e:
                db.session.rollback()
                raise e
        return wrapper
    return decorator