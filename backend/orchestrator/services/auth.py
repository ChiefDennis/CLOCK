from functools import wraps
from flask import jsonify
from flask_jwt_extended import create_access_token, get_jwt, verify_jwt_in_request
from models import User

# System-wide permissions
PERMISSIONS = {
    "get_key",
    "create_key",
    "list_keys",
    "set_enabled",
    "delete_key",
    "set_rotation",
    "manage_users",
    "use_key"
}

# Role-based access control (RBAC) mapping
ROLE_PERMISSIONS = {
    "user": {"get_key", "list_keys", "use_key"},
    # Grant the new permission to the admin role
    "admin": {
        "get_key", 
        "create_key", 
        "list_keys", 
        "set_enabled", 
        "delete_key", 
        "set_rotation", 
        "manage_users",
        "use_key"
        }
}


def authenticate_user(username, password):
    """
    Verifies user credentials and status using the database.
    Returns a dict with user info if valid, else None.
    """
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password) and user.enabled:
        return {"username": user.username, "role": user.role}

    return None


def generate_token(user):
    """
    Generates a JWT with the username as subject and role as additional claim.
    """
    return create_access_token(
        identity=user["username"],
        additional_claims={"role": user["role"]}
    )


def require_permission(permission):
    """
    Decorator to enforce that the JWT contains a role with the required permission.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Validate JWT presence and validity
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")

            if role not in ROLE_PERMISSIONS or permission not in ROLE_PERMISSIONS[role]:
                return jsonify(msg="Permission denied"), 403

            return fn(*args, **kwargs)

        return decorator
    return wrapper
