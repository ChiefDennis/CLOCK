# Routes for sensitive operations

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import g, jsonify
from datetime import datetime, timezone
from services.auth import require_permission
from services.logger import log_request_response
from models import PendingAction, db
from schemas.error_schemas import ErrorSchema
from schemas.request_schemas import MessageSchema, PendingActionSchema
action_bp = Blueprint("Actions", "actions", url_prefix="/api", description="Approve or reject pending sensitive actions")

@action_bp.route("/pending-actions")
class PendingActionList(MethodView):
    @log_request_response("List Pending Actions")
    @require_permission("manage_users")
    @action_bp.response(200, PendingActionSchema(many=True))
    @action_bp.response(422, ErrorSchema)
    def get(self):
        """List all actions awaiting approval (Admin only)"""
        # For now it will query all actions not only awaiting approval
        #actions = PendingAction.query.filter_by(status='PENDING').all()
        actions = PendingAction.query.all()
        schema = PendingActionSchema(many=True)
        serialized_actions = schema.dump(actions)
        return jsonify(serialized_actions)

@action_bp.route("/pending-actions/<int:action_id>/approve")
class ApproveAction(MethodView):
    @log_request_response("Approve Pending Action")
    @require_permission("manage_users")
    @action_bp.response(200, MessageSchema)
    @action_bp.response(422, ErrorSchema)
    def post(self, action_id):
        """Approve a pending action (Admin only)"""
        action = PendingAction.query.get_or_404(action_id)
        reviewer_username = g.current_user

        if action.status != 'PENDING':
            abort(409, message="This action is not pending approval.")

        if action.created_by_username == reviewer_username:
            abort(403, message="You cannot approve your own request.")

        action.status = 'APPROVED'
        action.reviewed_by_username = reviewer_username
        action.reviewed_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            "message": f"Action {action_id} approved. It will be executed by the background worker shortly."
        })


@action_bp.route("/pending-actions/<int:action_id>/deny")
class DenyAction(MethodView):
    @log_request_response("Deny Pending Action")
    @require_permission("manage_users")
    @action_bp.response(200, MessageSchema)
    @action_bp.response(422, ErrorSchema)
    def post(self, action_id):
        """Deny a pending action (Admin only)"""
        action = PendingAction.query.get_or_404(action_id)
        reviewer_username = g.current_user

        if action.status != 'PENDING':
            abort(409, message="This action is not pending approval.")

        if action.created_by_username == reviewer_username:
            abort(403, message="You cannot deny your own request.")

        action.status = 'DENIED'
        action.reviewed_by_username = reviewer_username
        action.reviewed_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            "message": f"Action {action_id} denied. It will not be executed."
        })