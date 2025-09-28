# /orchestrator/routes/admin_routes.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify, Response, request


from marshmallow import ValidationError
from flask import make_response

from extensions import db
from services.auth import require_permission
from services.logger import log_request_response
from services import metadata_service, cbom_service
from cyclonedx.output import make_outputter, OutputFormat, SchemaVersion
from models import Log, ModuleStatus, Alarm
from schemas.module_schemas import ModuleStatusSchema
from schemas.error_schemas import ErrorSchema
from schemas.request_schemas import (
    SyncSchema, 
    LogQuerySchema, 
    PaginatedLogResponseSchema, 
    SyncSummarySchema,
    AlarmQuerySchema,
    PaginatedAlarmResponseSchema,
    AlarmSchema,
)

admin_bp = Blueprint("Admin", "admin", url_prefix="/api", description="Administrative and operational endpoints")

@admin_bp.route("/logs")
class LogsView(MethodView):
    @log_request_response("List Logs")
    @require_permission("manage_users")
    @admin_bp.arguments(LogQuerySchema, location="query")
    @admin_bp.response(200, PaginatedLogResponseSchema)
    @admin_bp.response(422, ErrorSchema)
    def get(self, args):
        """Gets a paginated list of the most recent logs (Admin only)."""
        page_size = args.get("page_size")
        page_token = args.get("page_token")

        query = Log.query.order_by(Log.id.desc())

        if page_token:
            query = query.filter(Log.id < page_token)

        logs = query.limit(page_size + 1).all()

        next_page_token = None
        if len(logs) > page_size:
            # The token for the next page is the ID of the *last item* on the current page.
            # The index is page_size - 1 because lists are zero-indexed.
            next_page_token = logs[page_size - 1].id
            logs_to_return = logs[:page_size]
        else:
            logs_to_return = logs

        # This is more robust and avoids the race condition.
        result = {
            "logs": [log.to_dict() for log in logs_to_return],
            "next_page_token": next_page_token
        }
        return jsonify(result)

@admin_bp.route("/alarms")
class AlarmList(MethodView):
    @log_request_response("List Alarms")
    @require_permission("manage_users")
    @admin_bp.arguments(AlarmQuerySchema, location="query")
    @admin_bp.response(200, PaginatedAlarmResponseSchema)
    @admin_bp.response(422, ErrorSchema)
    def get(self, args):
        """Gets a paginated list of the most recent alarms (Admin only)."""
        page_size = args.get("page_size")
        page_token = args.get("page_token")

        query = Alarm.query.order_by(Alarm.id.desc())

        if page_token:
            query = query.filter(Alarm.id < page_token)

        alarms = query.limit(page_size + 1).all()

        next_page_token = None
        if len(alarms) > page_size:
            next_page_token = alarms[page_size-1].id
            alarms_to_return = alarms[:page_size]
        else:
            alarms_to_return = alarms

        # Manually serialize the data and return it with jsonify.
        result = {
            "alarms": [
                {
                    "id": alarm.id,
                    "timestamp": alarm.timestamp.isoformat(),
                    "severity": alarm.severity,
                    "event_type": alarm.event_type,
                    "message": alarm.message,
                    "is_acknowledged": alarm.is_acknowledged
                } for alarm in alarms_to_return
            ],
            "next_page_token": next_page_token
        }
        return jsonify(result)
    
@admin_bp.route("/alarms/<int:alarm_id>")
class AlarmDetail(MethodView):
    @log_request_response("Update Alarm Status") # Renamed for clarity
    @require_permission("manage_users")
    @admin_bp.response(200, AlarmSchema)
    def patch(self, alarm_id):
        """Updates a specific alarm's acknowledged status."""
        alarm = Alarm.query.get_or_404(alarm_id)
        
        # Get the JSON data from the request body
        data = request.get_json()
        
        # Check if 'is_acknowledged' is in the request and update the alarm
        if 'is_acknowledged' in data and isinstance(data['is_acknowledged'], bool):
            alarm.is_acknowledged = data['is_acknowledged']
        else:
            # If the body is invalid, return an error
            return jsonify({"error": "Invalid request body. 'is_acknowledged' must be a boolean."}), 400
        
        db.session.add(alarm)
        db.session.commit()
        
        # Manually serialize and return the updated alarm
        updated_alarm_data = {
            "id": alarm.id,
            "timestamp": alarm.timestamp.isoformat(),
            "severity": alarm.severity,
            "event_type": alarm.event_type,
            "message": alarm.message,
            "is_acknowledged": alarm.is_acknowledged
        }
        return jsonify(updated_alarm_data)

@admin_bp.route("/sync")
class SyncView(MethodView):
    @log_request_response("Provider Key Synchronization")
    @require_permission("manage_users")
    @admin_bp.arguments(SyncSchema)
    @admin_bp.response(200, SyncSummarySchema)
    @admin_bp.response(422, ErrorSchema)

    def post(self, sync_data):
        """Synchronizes the local database with the state of a cloud provider."""
        provider = sync_data["cloud_provider"]
        try:
            summary = metadata_service.synchronize_provider_keys(provider)
            return jsonify({
                "provider": provider,
                "status": "Synchronization successful",
                "summary": summary
            })
        except Exception as e:
            abort(500, message=f"Synchronization failed for {provider}: {str(e)}")

@admin_bp.route("/modules/status")
class ModuleStatusList(MethodView):
    @log_request_response("List Module Statuses")
    @require_permission("manage_users")
    @admin_bp.response(200, ModuleStatusSchema(many=True))
    def get(self):
        """Get the enabled/disabled status of all modules (Admin only)"""
        return ModuleStatus.query.all()

@admin_bp.route("/modules/status/<string:provider_name>")
class ModuleStatusDetail(MethodView):
    """Manage the status of a specific module."""

    @log_request_response("Update Module Status")
    @require_permission("manage_users")
    @admin_bp.arguments(ModuleStatusSchema)
    @admin_bp.response(200, ModuleStatusSchema)
    @admin_bp.response(422, ErrorSchema)
    def patch(self, update_data, provider_name):
        module = ModuleStatus.query.filter_by(provider_name=provider_name).first_or_404()
        module.is_enabled = update_data["is_enabled"]
        db.session.commit()
        db.session.refresh(module)

        # Return a plain dict (not a model). This helps the decorator do its job.
        return jsonify({
            "provider_name": module.provider_name,
            "is_enabled": bool(module.is_enabled),
            "last_synced_at": module.last_synced_at.isoformat() if module.last_synced_at else None
        })



@admin_bp.route("/cbom")
class CBOMView(MethodView):
    @log_request_response("CBOM Report Generation")
    @require_permission("manage_users")
    @admin_bp.response(200)
    @admin_bp.response(422, ErrorSchema)
    def get(self):
        """
        Generates a synchronized Cryptographic Bill of Materials (CBOM) report
        in the CycloneDX standard format.
        """
        try:
            # --- Sync logic ---
            providers = ["aws", "gcp", "azure"]
            for provider in providers:
                try:
                    module_status = ModuleStatus.query.filter_by(provider_name=provider).first()
                    if module_status and module_status.is_enabled:
                        metadata_service.synchronize_provider_keys(provider)
                except Exception as e:
                    print(f"[CBOM Warning] Failed to sync {provider}: {str(e)}")

            # --- BOM generation ---
            bom = cbom_service.build_cbom_report()

            # ---Rendering Logic ---
            output_format_str = request.args.get("format", "json").lower()
            output_format = OutputFormat.JSON if output_format_str == "json" else OutputFormat.XML

            outputter = make_outputter(bom, output_format, SchemaVersion.V1_6)
            report_body = outputter.output_as_string(indent=2)
            mimetype = "application/json" if output_format_str == "json" else "application/xml"

            return Response(report_body, mimetype=mimetype, status=200)

        except Exception as e:
            abort(500, message=f"Failed to generate CBOM: {e}")