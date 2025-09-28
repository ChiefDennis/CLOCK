# /modules/azure/routes/azure_internal_routes.py

from flask import Blueprint, request, jsonify
from services.logic import (
    create_key, 
    get_key, list_keys, 
    set_enabled, 
    set_rotation, 
    delete_key,
    encrypt,
    decrypt
)

azure_bp = Blueprint("azure_internal_routes", __name__)

@azure_bp.route("/create-key", methods=["POST"])
def create_key_route():
    data = request.get_json(force=True) or {}
    key, status_code = create_key(data)
    return jsonify(key), status_code

@azure_bp.route("/get-key", methods=["POST"])
def get_key_route():
    data = request.get_json(force=True) or {}
    key, status_code = get_key(data)
    return jsonify(key), status_code

@azure_bp.route("/list-keys", methods=["GET"])
def list_keys_route():
    # Azure list doesn't use tokens, but we accept the param for compatibility
    keys, status_code = list_keys()
    return jsonify(keys), status_code

@azure_bp.route("/set-enabled", methods=["POST"])
def set_enabled_route():
    data = request.get_json(force=True) or {}
    key, status_code = set_enabled(data)
    return jsonify(key), status_code

@azure_bp.route("/set-rotation", methods=["POST"])
def set_rotation_route():
    data = request.get_json(force=True) or {}
    result, status_code = set_rotation(data)
    return jsonify(result), status_code

@azure_bp.route("/delete-key", methods=["POST"])
def delete_key_route():
    data = request.get_json(force=True) or {}
    result, status_code = delete_key(data)
    return jsonify(result), status_code

@azure_bp.route("/encrypt", methods=["POST"])
def encrypt_route():
    data = request.get_json(force=True) or {}
    key, status_code = encrypt(data)
    return jsonify(key), status_code

@azure_bp.route("/decrypt", methods=["POST"])
def decrypt_route():
    data = request.get_json(force=True) or {}
    key, status_code = decrypt(data)
    return jsonify(key), status_code