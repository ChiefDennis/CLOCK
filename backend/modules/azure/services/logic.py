import os, uuid, base64
from datetime import timedelta
from azure.keyvault.keys import KeyClient, KeyType
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.keyvault.keys.crypto import CryptographyClient, EncryptionAlgorithm

def _format_key_response(key_vault_key):
    """Formats a KeyVaultKey object into the dict structure the orchestrator expects."""
    # The orchestrator's converter expects a specific nested structure.
    return {
        "key": {
            "kid": key_vault_key.id,
            "kty": key_vault_key.key_type,
            "key_ops": key_vault_key.key_operations
        },
        "attributes": {
            "enabled": key_vault_key.properties.enabled,
            "created": key_vault_key.properties.created_on.timestamp(),
            "updated": key_vault_key.properties.updated_on.timestamp(),
            "recoveryLevel": key_vault_key.properties.recovery_level
        },
        "tags": key_vault_key.properties.tags
    }

def _get_key_client():
    """
    Initializes and returns an Azure Key Vault KeyClient.
    Switches between the emulator (mock mode) and the real Azure API
    based on the AZURE_KV_URL environment variable.
    """
    vault_url = os.getenv("AZURE_KV_URL")
    credential = None
    kwargs = {}

    if vault_url:
        # --- MOCK MODE ---
        print("[INFO] Azure module is in MOCK MODE.")
        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID", "demo"),
            client_id=os.getenv("AZURE_CLIENT_ID", "demo"),
            client_secret=os.getenv("AZURE_CLIENT_SECRET", "demo")
        )
        # This tells the client to trust our newly generated certificate.
        kwargs['verify'] = os.getenv("REQUESTS_CA_BUNDLE")
    else:
        # --- REAL API MODE ---
        print("[INFO] Azure module is in REAL API MODE.")
        vault_name = os.getenv("AZURE_VAULT_NAME")
        if not vault_name:
            raise ValueError("AZURE_VAULT_NAME environment variable is not set.")
        vault_url = f"https://{vault_name}.vault.azure.net"
        credential = DefaultAzureCredential()

    return KeyClient(vault_url=vault_url, credential=credential, **kwargs)

def create_key(payload):
    key_client = _get_key_client()
    key_name = f"key-{uuid.uuid4()}"
    
    key_type = "oct-HSM" if payload.get("protection_level") == "HSM" else KeyType.OCT
    
    try:
        key = key_client.create_key(name=key_name, key_type=key_type, tags=payload.get("labels", {}))
        return _format_key_response(key), 200
    except HttpResponseError as e:
        return {"error": str(e)}, e.status_code

def get_key(payload):
    key_client = _get_key_client()
    key_name = payload.get("key_id")
    if not key_name:
        return {"error": "key_id is required"}, 400
    try:
        key = key_client.get_key(key_name)
        return _format_key_response(key), 200
    except ResourceNotFoundError:
        return {"error": f"Key '{key_name}' not found."}, 404
    except HttpResponseError as e:
        return {"error": str(e)}, e.status_code

def list_keys():
    key_client = _get_key_client()
    try:
        keys_properties = key_client.list_properties_of_keys()
        # We need to fetch each full key to provide complete details
        key_list = [
            _format_key_response(key_client.get_key(prop.name))
            for prop in keys_properties
        ]
        return {"keys": key_list}, 200
    except HttpResponseError as e:
        return {"error": str(e)}, e.status_code

def set_enabled(payload):
    key_client = _get_key_client()
    key_name = payload.get("key_id")
    enabled = payload.get("enabled")
    if not key_name or enabled is None:
        return {"error": "key_id and enabled are required"}, 400
    try:
        updated_properties = key_client.update_key_properties(name=key_name, enabled=bool(enabled))
        key = key_client.get_key(key_name) # Fetch the full key again to return it
        return _format_key_response(key), 200
    except ResourceNotFoundError:
        return {"error": f"Key '{key_name}' not found."}, 404
    except HttpResponseError as e:
        return {"error": str(e)}, e.status_code

def set_rotation(payload):
    key_client = _get_key_client()
    key_name = payload.get("key_id")
    enabled = payload.get("enabled")
    days = payload.get("rotation_days")

    if not key_name or enabled is None:
        return {"error": "key_id and enabled are required"}, 400
    try:
        if enabled:
            # Set rotation to X days, or a default of 90 if not provided
            time_after_create = f"P{int(days or 90)}D"
            policy = key_client.update_key_rotation_policy(
                key_name=key_name,
                expires_in=timedelta(days=int(days or 90) + 7), # Key expires 7 days after rotation
                time_after_create=time_after_create
            )
            return {"status": "Rotation enabled", "policy_id": policy.id}, 200
        else:
            # An empty policy with no actions disables rotation
            policy = key_client.update_key_rotation_policy(key_name=key_name, actions=[])
            return {"status": "Rotation disabled", "policy_id": policy.id}, 200

    except ResourceNotFoundError:
        return {"error": f"Key '{key_name}' not found."}, 404
    except HttpResponseError as e:
        return {"error": str(e)}, e.status_code

def delete_key(payload):
    key_client = _get_key_client()
    key_name = payload.get("key_id")
    if not key_name:
        return {"error": "key_id is required"}, 400
    try:
        poller = key_client.begin_delete_key(key_name)
        deleted_key = poller.result()
        return {"status": "Deletion scheduled", "recoveryId": deleted_key.recovery_id}, 200
    except ResourceNotFoundError:
        return {"error": f"Key '{key_name}' not found."}, 404
    except HttpResponseError as e:
        return {"error": str(e)}, e.status_code
    
def encrypt(payload):
    """Encrypts plaintext using an Azure Key Vault key."""
    key_client = _get_key_client()
    key_name = payload.get("key_id")
    plaintext = payload.get("plaintext")

    # The CryptographyClient is a sub-client used for crypto operations.
    # We get the full key ID (the URI) to initialize it.
    key = key_client.get_key(key_name)
    crypto_client = CryptographyClient(key, key_client.credential)

    # The plaintext must be converted to bytes.
    plaintext_bytes = plaintext.encode('utf-8')
    
    # For symmetric keys, AES-256 is a standard choice.
    result = crypto_client.encrypt(EncryptionAlgorithm.A256CBC_PAD, plaintext_bytes)
    
    # The result's ciphertext is raw bytes; we base64-encode it for JSON.
    ciphertext_b64 = base64.b64encode(result.ciphertext).decode('utf-8')
    
    return {"ciphertext": ciphertext_b64}, 200

def decrypt(payload):
    """Decrypts a base64-encoded ciphertext using an Azure Key Vault key."""
    key_client = _get_key_client()
    key_name = payload.get("key_id")
    ciphertext = payload.get("ciphertext")

    key = key_client.get_key(key_name)
    crypto_client = CryptographyClient(key, key_client.credential)
    
    # The incoming ciphertext is a base64 string; we must decode it into bytes.
    ciphertext_blob = base64.b64decode(ciphertext)
    
    result = crypto_client.decrypt(EncryptionAlgorithm.A256CBC_PAD, ciphertext_blob)
    
    # The resulting plaintext is raw bytes; we decode it back into a string.
    plaintext = result.plaintext.decode('utf-8')

    return {"plaintext": plaintext}, 200