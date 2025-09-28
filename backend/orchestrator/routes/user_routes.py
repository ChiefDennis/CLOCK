# /orchestrator/routes/user_routes.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import g, jsonify
from datetime import datetime, timedelta

from services.auth import require_permission
from services.logger import log_request_response
from models import User, PendingAction
from extensions import db
from schemas.user_schemas import UserSchema, UserCreateSchema, UserUpdateSchema
from schemas.error_schemas import ErrorSchema

user_bp = Blueprint("Users", "users", url_prefix="/api", description="Operations on users")

@user_bp.route("/users")
class UserList(MethodView):
    @log_request_response("List Users Attempt")
    @require_permission("manage_users")
    @user_bp.response(200, UserSchema(many=True))
    @user_bp.response(422, ErrorSchema)
    def get(self):
        """List all users (Admin only)"""
        # Step 1: Fetch all user objects from the database.
        users = User.query.all()
        
        # Step 2: Manually serialize the list of user objects into a list of dictionaries.
        # This ensures we are not relying on implicit behavior.
        result = [
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "enabled": user.enabled
            } for user in users
        ]
        
        # Step 3: Return a proper Flask JSON response object.
        return jsonify(result)

    @log_request_response(
        "User Creation Attempt",
        hide_request_fields=["password"]
    )
    @require_permission("manage_users")
    @user_bp.arguments(UserCreateSchema)
    @user_bp.response(201, UserSchema)
    def post(self, new_user_data):
        """Create a new user (Admin only)"""
        if User.query.filter_by(username=new_user_data["username"]).first():
            abort(409, message=f"User '{new_user_data['username']}' already exists.")
        
        user = User(
            username=new_user_data["username"],
            role=new_user_data["role"]
        )
        user.set_password(new_user_data["password"])
        db.session.add(user)
        db.session.commit()
        return user

@user_bp.route("/users/<int:user_id>")
class UserView(MethodView):
    @log_request_response("User Update Attempt", hide_request_fields=["password"])
    @require_permission("manage_users")
    @user_bp.arguments(UserUpdateSchema)
    @user_bp.response(200, UserSchema)
    @user_bp.response(422, ErrorSchema)
    def patch(self, update_data, user_id):
        """Update an existing user (Admin only)"""
        user = User.query.get_or_404(user_id)
        
        if "username" in update_data and update_data["username"] != user.username:
            if User.query.filter_by(username=update_data["username"]).first():
                abort(409, message=f"User '{update_data['username']}' already exists.")
            user.username = update_data["username"]
        if "password" in update_data:
            user.set_password(update_data["password"])
        if "role" in update_data:
            user.role = update_data["role"]
        if "enabled" in update_data:
            user.enabled = update_data["enabled"]
            
        db.session.commit()
        result = {
            "id":  user.id,
            "username": user.username,
            "role": user.role,
            "enabled": user.enabled
        }
        return jsonify(result)

    @log_request_response("User Deletion Request")
    @require_permission("manage_users")
    @user_bp.response(202)
    def delete(self, user_id):
        """Request deletion of a user (requires second admin approval)"""
        user_to_delete = User.query.get_or_404(user_id)
        current_admin_username = g.current_user

        if current_admin_username == user_to_delete.username:
            abort(403, message="Admin cannot delete their own account.")

        action = PendingAction(
            action_type='DELETE_USER',
            resource_identifier=str(user_id),
            created_by_username=current_admin_username,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(action)
        db.session.commit()

        return jsonify({
            "message": "User deletion requested. A second admin must approve.",
            "action_id": action.id
        })