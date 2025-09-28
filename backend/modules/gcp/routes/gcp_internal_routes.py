# /modules/gcp/routes/gcp_internal_routes.py

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

gcp_bp = Blueprint("gcp_internal_routes", __name__)

@gcp_bp.route("/create-key", methods=["POST"])
def create_key_route():
    data = request.get_json(force=True) or {}
    return jsonify(create_key(data))

@gcp_bp.route("/get-key", methods=["POST"])
def get_key_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    if not key_id:
        return jsonify({"error": "key_id is required"}), 400
    return jsonify(get_key(key_id))

@gcp_bp.route("/list-keys", methods=["GET"])
def list_keys_route():
    page_size = request.args.get("page_size", default=100, type=int)
    page_token = request.args.get("page_token")
    return jsonify(list_keys(page_size=page_size, page_token=page_token))

@gcp_bp.route("/set-enabled", methods=["POST"])
def set_enabled_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    enabled = data.get("enabled")
    if key_id is None or enabled is None:
        return jsonify({"error": "key_id and enabled are required"}), 400
    return jsonify(set_enabled(key_id, bool(enabled)))

@gcp_bp.route("/set-rotation", methods=["POST"])
def set_rotation_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    enabled = data.get("enabled")
    rotation_days = data.get("rotation_days")
    if key_id is None or enabled is None:
        return jsonify({"error": "key_id and enabled are required"}), 400
    return jsonify(set_rotation(key_id, bool(enabled), rotation_days))

@gcp_bp.route("/delete-key", methods=["POST"])
def delete_key_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    schedule_days = data.get("schedule_days")
    if not key_id:
        return jsonify({"error": "key_id is required"}), 400
    return jsonify(delete_key(key_id, schedule_days))

@gcp_bp.route("/encrypt", methods=["POST"])
def encrypt_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    plaintext = data.get("plaintext")
    if not key_id or plaintext is None:
        return jsonify({"error": "key_id and plaintext are required"}), 400
    return jsonify(encrypt(key_id, plaintext))

@gcp_bp.route("/decrypt", methods=["POST"])
def decrypt_route():
    data = request.get_json(force=True) or {}
    key_id = data.get("key_id")
    ciphertext = data.get("ciphertext")
    if not key_id or not ciphertext:
        return jsonify({"error": "key_id and ciphertext are required"}), 400
    return jsonify(decrypt(key_id, ciphertext))