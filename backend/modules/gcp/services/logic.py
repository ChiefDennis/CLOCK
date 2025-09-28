import os, uuid, base64
from google.cloud import kms_v1
from google.auth.credentials import AnonymousCredentials
from google.protobuf import duration_pb2, field_mask_pb2

# --- Internals & Helpers ---

def _kms_client():
    """
    Initializes the GCP KMS client. In a mock environment, it uses a
    REST transport and anonymous credentials to connect to the mock server.
    """
    mock_endpoint = os.getenv("GCP_KMS_BASE_URL")
    
    if mock_endpoint:
        # For mocks, we need BOTH client_options and AnonymousCredentials.
        return kms_v1.KeyManagementServiceClient(
            credentials=AnonymousCredentials(),
            client_options={"api_endpoint": mock_endpoint}
        )
    else:
        # In a real environment, the client handles credentials automatically.
        return kms_v1.KeyManagementServiceClient()


def _key_ring_name():
    """Constructs the parent KeyRing resource name from environment variables."""
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION")
    keyring_id = os.getenv("GCP_KEYRING_ID")
    if not all([project_id, location, keyring_id]):
        raise EnvironmentError("GCP_PROJECT_ID, GCP_LOCATION, and GCP_KEYRING_ID must be set.")
    return f"projects/{project_id}/locations/{location}/keyRings/{keyring_id}"


def _get_full_key_details(kms_client, key_name):
    """Fetches a key and its primary version, returning a consolidated dict."""
    key = kms_client.get_crypto_key(name=key_name)
    primary_version = kms_client.get_crypto_key_version(name=key.primary.name)
    
    key_dict = kms_v1.CryptoKey.to_dict(key)
    key_dict["primary"] = kms_v1.CryptoKeyVersion.to_dict(primary_version)
    return key_dict

# --- Public API ---

def create_key(payload):
    """Creates a new CryptoKey in GCP KMS."""
    kms = _kms_client()
    parent = _key_ring_name()
    key_id = f"key-{uuid.uuid4()}"

    purpose = kms_v1.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT
    algorithm = kms_v1.CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION
    protection_level = kms_v1.ProtectionLevel[payload.get("protection_level", "SOFTWARE")]

    key = {
        "purpose": purpose,
        "version_template": {
            "algorithm": algorithm,
            "protection_level": protection_level,
        },
        "labels": payload.get("labels", {})
    }
    
    created_key = kms.create_crypto_key(request={"parent": parent, "crypto_key_id": key_id, "crypto_key": key})
    return _get_full_key_details(kms, created_key.name)


def get_key(key_ref):
    """Retrieves a single CryptoKey and its primary version details."""
    kms = _kms_client()
    return _get_full_key_details(kms, key_ref)


def list_keys(page_size=100, page_token=None):
    """Lists all CryptoKeys in the configured KeyRing."""
    kms = _kms_client()
    parent = _key_ring_name()
    response = kms.list_crypto_keys(request={"parent": parent, "page_size": page_size, "page_token": page_token})
    keys = [_get_full_key_details(kms, key.name) for key in response.crypto_keys]
    return {"keys": keys, "next_token": response.next_page_token}


def set_enabled(key_ref, enabled):
    """Enables or disables the primary version of a CryptoKey."""
    kms = _kms_client()
    key = kms.get_crypto_key(name=key_ref)
    primary_version_name = key.primary.name
    new_state = kms_v1.CryptoKeyVersion.CryptoKeyVersionState.ENABLED if enabled else kms_v1.CryptoKeyVersion.CryptoKeyVersionState.DISABLED
    
    kms.update_crypto_key_version(
        request={
            "crypto_key_version": {"name": primary_version_name, "state": new_state},
            "update_mask": field_mask_pb2.FieldMask(paths=["state"]),
        }
    )
    return _get_full_key_details(kms, key_ref)


def set_rotation(key_ref, enabled, rotation_days=365):
    """Sets the automatic rotation schedule for a CryptoKey."""
    kms = _kms_client()
    update_paths = []
    key_update = {"name": key_ref}
    
    if enabled:
        rotation_period_seconds = int(rotation_days or 365) * 86400
        key_update["rotation_period"] = duration_pb2.Duration(seconds=rotation_period_seconds)
        update_paths.append("rotation_period")
        update_paths.append("next_rotation_time") 
    else:
        key_update["rotation_period"] = None
        update_paths.append("rotation_period")

    kms.update_crypto_key(
        request={
            "crypto_key": key_update,
            "update_mask": field_mask_pb2.FieldMask(paths=update_paths),
        }
    )
    return _get_full_key_details(kms, key_ref)


def delete_key(key_ref, schedule_days=None):
    """Schedules the primary version of a key for destruction."""
    kms = _kms_client()
    key = kms.get_crypto_key(name=key_ref)
    primary_version_name = key.primary.name
    kms.destroy_crypto_key_version(request={"name": primary_version_name})
    return _get_full_key_details(kms, key_ref)

def encrypt(key_ref, plaintext):
    """Encrypts plaintext using GCP KMS and returns a base64-encoded ciphertext."""
    kms = _kms_client()
    
    # The plaintext must be converted to bytes for the API call.
    plaintext_bytes = plaintext.encode('utf-8')
    
    response = kms.encrypt(request={"name": key_ref, "plaintext": plaintext_bytes})
    
    # The 'ciphertext' from the response is raw bytes; we base64-encode it for JSON.
    ciphertext_b64 = base64.b64encode(response.ciphertext).decode('utf-8')
    
    return {"ciphertext": ciphertext_b64}

def decrypt(key_ref, ciphertext):
    """Decrypts a base64-encoded ciphertext using GCP KMS."""
    kms = _kms_client()

    # The incoming ciphertext is a base64 string; we must decode it into bytes.
    ciphertext_blob = base64.b64decode(ciphertext)

    response = kms.decrypt(request={"name": key_ref, "ciphertext": ciphertext_blob})

    # The resulting 'plaintext' is raw bytes; we decode it back into a string.
    plaintext = response.plaintext.decode('utf-8')
    
    return {"plaintext": plaintext}