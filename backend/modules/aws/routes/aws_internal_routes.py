from flask import Blueprint, request, jsonify
from services.logic import (
    create_key,
    get_key,
    list_keys,
    set_enabled,
    set_rotation,
    delete_key,
    encrypt,
    decrypt
)

aws_bp = Blueprint("aws_internal_routes", __name__)

@aws_bp.route("/create-key", methods=["POST"])
def create_key_route():
    data = request.get_json(force=True) or {}
    return jsonify(create_key(data))

@aws_bp.route("/get-key", methods=["POST"])
def get_key_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    if not key_id:
        return jsonify({"error": "key_id is required"}), 400
    return jsonify(get_key(key_id))  # accepts KeyId or ARN string

@aws_bp.route("/list-keys", methods=["GET"])
def list_keys_route():
    page_size = request.args.get("page_size", default=100, type=int)
    page_token = request.args.get("page_token")
    return jsonify(list_keys(page_size=page_size, page_token=page_token))

@aws_bp.route("/set-enabled", methods=["POST"])
def set_enabled_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    enabled = data.get("enabled")
    if key_id is None or enabled is None:
        return jsonify({"error": "key_id and enabled are required"}), 400
    return jsonify(set_enabled(key_id, bool(enabled)))

@aws_bp.route("/set-rotation", methods=["POST"])
def set_rotation_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    enabled = data.get("enabled")
    rotation_days = data.get("rotation_days")
    if key_id is None or enabled is None:
        return jsonify({"error": "key_id and enabled are required"}), 400
    return jsonify(set_rotation(key_id, bool(enabled), rotation_days))

@aws_bp.route("/delete-key", methods=["POST"])
def delete_key_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    schedule_days = data.get("schedule_days", 7)
    if not key_id:
        return jsonify({"error": "key_id is required"}), 400
    return jsonify(delete_key(key_id, schedule_days))

@aws_bp.route("/encrypt", methods=["POST"])
def encrypt_route():
    data = request.get_json(force=True) or {}
    try:
        result, status_code = encrypt(data)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aws_bp.route("/decrypt", methods=["POST"])
def decrypt_route():
    data = request.get_json(force=True) or {}
    try:
        result, status_code = decrypt(data)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500