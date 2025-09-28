# /orchestrator/routes/key_routes.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify, g
from datetime import datetime, timedelta, timezone 

from common.utils import get_converter
from extensions import db
from models import KeyMetadata
from services.auth import require_permission
from services.logic import forward_request
from services.logger import log_request_response
from services import metadata_service
from schemas.error_schemas import ErrorSchema
from schemas.request_schemas import (
    CreateKeySchema,
    GetKeySchema,
    ListKeysQuerySchema,
    SetEnabledSchema,
    SetRotationSchema,
    DeleteKeySchema,
    ListLocalKeysQuerySchema,
    EncryptSchema,
    DecryptSchema,
    EncryptResponseSchema,
    DecryptResponseSchema
)

key_bp = Blueprint("Keys", "keys", url_prefix="/api", description="Operations on cryptographic keys")

# A central helper to handle request forwarding and error propagation.
def handle_forward_request(endpoint, data, method="POST"):
    """Forwards the request and aborts with the downstream error if it fails."""
    response, status_code = forward_request(endpoint, data, method=method)
    if status_code >= 400:
        # If the cloud module returned an error, we abort our own request
        # and pass the error message and status code up to the client.
        abort(status_code, message=response.get("error", "An unknown error occurred in the downstream service."))
    # On success, just return the JSON body.
    return response

@key_bp.route("/get-key")
class GetKey(MethodView):
    @log_request_response("Get Key")
    @require_permission("get_key")
    @key_bp.arguments(GetKeySchema)
    @key_bp.response(200)
    def post(self, data):
        """Fetches provider key metadata and syncs with local DB."""
        # The helper function handles the request and aborts on failure.
        response = handle_forward_request("get-key", data)
        
        # This code only runs on a successful response.
        try:
            converter = get_converter(data["cloud_provider"])
            if converter:
                metadata_obj = converter(response)
                metadata_obj.last_updated_by = g.current_user
                metadata_obj.last_update_source = 'API'
                metadata_service.upsert_key(metadata_obj)
        except Exception as e:
            print(f"[Warning] Failed to sync key metadata on get-key: {e}")
            
        return jsonify(response)

@key_bp.route("/create-key")
class CreateKey(MethodView):
    @log_request_response("Create Key")
    @require_permission("create_key")
    @key_bp.arguments(CreateKeySchema)
    @key_bp.response(200)
    def post(self, data):
        """Creates a key and stores its metadata in the local DB."""
        response = handle_forward_request("create-key", data)
        
        try:
            converter = get_converter(data["cloud_provider"])
            if converter:
                metadata_obj = converter(response)
                metadata_obj.last_updated_by = g.current_user
                metadata_obj.last_update_source = 'API'
                metadata_service.upsert_key(metadata_obj)
        except Exception as e:
            print(f"[Warning] Failed to sync key metadata on create-key: {e}")
            
        return jsonify(response)

@key_bp.route("/list-keys")
class ListKeys(MethodView):
    @log_request_response("List Cloud Keys")
    @require_permission("list_keys")
    @key_bp.arguments(ListKeysQuerySchema, location="query")
    @key_bp.response(200)
    def get(self, args):
        """Lists keys from the cloud provider. Does not sync with the database."""
        response = handle_forward_request("list-keys", args, method="GET")
        return jsonify(response)

@key_bp.route("/list-local-keys")
class ListLocalKeys(MethodView):
    @log_request_response("List Local Keys from DB")
    @require_permission("list_keys")
    @key_bp.arguments(ListLocalKeysQuerySchema, location="query")
    @key_bp.response(200)
    def get(self, args):
        """Lists key metadata stored in the local database with optional filtering."""
        keys = metadata_service.list_local_keys(filters=args)
        return jsonify([key.to_dict() for key in keys])

@key_bp.route("/set-enabled")
class SetEnabled(MethodView):
    @log_request_response("Set Enabled")
    @require_permission("set_enabled")
    @key_bp.arguments(SetEnabledSchema)
    @key_bp.response(200)
    def post(self, data):
        """Enables or disables the specified key."""
        response = handle_forward_request("set-enabled", data)
        
        key = KeyMetadata.query.filter_by(
            cloud_provider=data['cloud_provider'], 
            key_id=data['key_id']
        ).first()
        if key:
            key.status = "Enabled" if data['enabled'] else "Disabled"
            key.last_updated_by = g.current_user
            key.last_update_source = 'API'
            db.session.commit()
        
        return jsonify(response)

@key_bp.route("/set-rotation")
class SetRotation(MethodView):
    @log_request_response("Set Rotation")
    @require_permission("set_rotation")
    @key_bp.arguments(SetRotationSchema)
    @key_bp.response(200)
    def post(self, data):
        """Turns key rotation on/off."""
        response = handle_forward_request("set-rotation", data)
        
        key = KeyMetadata.query.filter_by(
            cloud_provider=data['cloud_provider'], 
            key_id=data['key_id']
        ).first()
        if key:
            key.rotation_enabled = data['enabled']
            key.last_updated_by = g.current_user
            key.last_update_source = 'API'
            db.session.commit()
        
        return jsonify(response)

@key_bp.route("/delete-key")
class DeleteKey(MethodView):
    @log_request_response("Delete Key")
    @require_permission("delete_key")
    @key_bp.arguments(DeleteKeySchema)
    @key_bp.response(200)
    def post(self, data):
        """Schedules deletion for the specified key."""
        response = handle_forward_request("delete-key", data)

        key = KeyMetadata.query.filter_by(
            cloud_provider=data['cloud_provider'], 
            key_id=data['key_id']
        ).first()

        if key:
            now_utc = datetime.now(timezone.utc)
            deletion_date = now_utc + timedelta(days=data['schedule_days'])
            
            # Combine status and timestamp into the status field
            key.status = f"PendingDeletion | {deletion_date.isoformat(timespec='seconds')}"

            key.last_updated_by = g.current_user
            key.last_update_source = 'API'
            db.session.commit()

        return jsonify(response)

@key_bp.route("/encrypt")
class Encrypt(MethodView):
    @log_request_response("Encrypt Data")
    @require_permission("use_key")
    @key_bp.arguments(EncryptSchema)
    @key_bp.response(200, EncryptResponseSchema)
    def post(self, data):
        """Encrypts plaintext data using a specified key."""
        return handle_forward_request("encrypt", data)

@key_bp.route("/decrypt")
class Decrypt(MethodView):
    @log_request_response("Decrypt Data")
    @require_permission("use_key")
    @key_bp.arguments(DecryptSchema)
    @key_bp.response(200, DecryptResponseSchema)
    def post(self, data):
        """Decrypts ciphertext using a specified key."""
        return handle_forward_request("decrypt", data)