import os, base64, boto3
from botocore.config import Config


# --- internals ---

def _kms_client():
    region = os.getenv("AWS_REGION", "us-east-1")
    endpoint = os.getenv("AWS_ENDPOINT_URL")
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "test")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

    cfg = Config(
        retries={"max_attempts": 2, "mode": "standard"},
        read_timeout=5,
        connect_timeout=3,
    )

    kwargs = {
        "region_name": region,
        "config": cfg,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
    }
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    return boto3.client("kms", **kwargs)


def _compat(md):
    out = dict(md)
    if "Arn" in out and "KeyArn" not in out:
        out["KeyArn"] = out["Arn"]
    if "Enabled" not in out and "KeyState" in out:
        out["Enabled"] = (out["KeyState"] == "Enabled")
    if "CustomerMasterKeySpec" not in out and "KeySpec" in out:
        out["CustomerMasterKeySpec"] = out["KeySpec"]
    return out


def _describe(kms, key_ref):
    """
    Describes a key and ALSO gets its rotation status, returning a merged dictionary.
    """
    # Step 1: Get the key's main descriptive metadata.
    resp = kms.describe_key(KeyId=key_ref)
    metadata = _compat(resp.get("KeyMetadata", {}))

    # Step 2: Make a second, separate call to get the key's rotation status.
    try:
        rotation_resp = kms.get_key_rotation_status(KeyId=key_ref)
        # Step 3: Merge the rotation status into the main metadata dictionary.
        if "RotationEnabled" in rotation_resp:
            metadata["RotationEnabled"] = rotation_resp["RotationEnabled"]
    except Exception as e:
        # If the call fails (e.g., for an asymmetric key), just log it and continue.
        print(f"[aws_module] Could not get rotation status for {key_ref}: {e}")

    return metadata


# --- public api ---

def create_key(payload):
    kms = _kms_client()
    params = {}
    
    # build the parameters for key creation
    params["KeySpec"] = "SYMMETRIC_DEFAULT" # AWS default for AES_256
    params["KeyUsage"] = payload.get("purpose", "ENCRYPT_DECRYPT")
    if "description" in payload:
        params["Description"] = payload["description"]
    if "labels" in payload:
        # Convert labels to the 'Tags' format AWS expects
        params["Tags"] = [{"TagKey": k, "TagValue": v} for k, v in payload["labels"].items()]

    # Step 1: Create the key
    resp = kms.create_key(**params)
    md = resp.get("KeyMetadata", {})

    if not md.get("KeyId"):
        # If creation failed, return the error response immediately
        return resp

    # Add a second step to handle rotation
    # Step 2: If rotation was requested, enable it on the new key.
    if payload.get("rotation_enabled") is True:
        try:
            print(f"[aws_module] Enabling rotation for new key {md['KeyId']}...")
            kms.enable_key_rotation(KeyId=md["KeyId"])
        except Exception as e:
            # Log a warning but don't fail the whole operation if rotation enabling fails
            print(f"[aws_module] WARNING: Key was created, but failed to enable rotation: {e}")

    # Return the final state of the key after all operations
    # Calling describe_key again ensures we get the updated rotation status.
    return _describe(kms, md["KeyId"])


def get_key(key_ref):
    kms = _kms_client()
    return _describe(kms, key_ref)


def list_keys(page_size=100, page_token=None):
    kms = _kms_client()
    kwargs = {}
    if page_size:
        kwargs["Limit"] = int(page_size)
    if page_token:
        kwargs["Marker"] = page_token
    resp = kms.list_keys(**kwargs)

    keys = []
    for item in resp.get("Keys", []):
        ref = item.get("KeyId") or item.get("KeyArn")
        keys.append(_describe(kms, ref))

    next_token = resp.get("NextMarker") if resp.get("Truncated") else None
    return {"keys": keys, "next_token": next_token}


def set_enabled(key_ref, enabled):
    kms = _kms_client()
    if enabled:
        kms.enable_key(KeyId=key_ref)
    else:
        kms.disable_key(KeyId=key_ref)
    return _describe(kms, key_ref)


def set_rotation(key_ref, enabled, rotation_days=None):
    # AWS rotation for symmetric keys is a simple toggle; ignore rotation_days.
    kms = _kms_client()
    if enabled:
        kms.enable_key_rotation(KeyId=key_ref)
    else:
        try:
            kms.disable_key_rotation(KeyId=key_ref)
        except Exception:
            pass
    return _describe(kms, key_ref)


def delete_key(key_ref, schedule_days=7):
    kms = _kms_client()
    # AWS requires 7..30 days; keep it simple
    try:
        pd = int(schedule_days)
    except Exception:
        pd = 7
    pd = max(7, min(30, pd))
    kms.schedule_key_deletion(KeyId=key_ref, PendingWindowInDays=pd)
    return _describe(kms, key_ref)


def encrypt(payload):
    """Encrypts plaintext using AWS KMS and returns a result and status code."""
    key_ref = payload.get("key_id")
    plaintext = payload.get("plaintext")
    if not key_ref or plaintext is None:
        raise ValueError("key_id and plaintext are required.")
    
    kms = _kms_client()
    plaintext_bytes = plaintext.encode('utf-8')
    response = kms.encrypt(KeyId=key_ref, Plaintext=plaintext_bytes)
    ciphertext_b64 = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
    
    return {"ciphertext": ciphertext_b64}, 200


def decrypt(payload):
    """Decrypts a base64-encoded ciphertext using AWS KMS."""
    key_ref = payload.get("key_id")
    ciphertext = payload.get("ciphertext")
    if not key_ref or not ciphertext:
        raise ValueError("key_id and ciphertext are required.")
        
    kms = _kms_client()
    ciphertext_blob = base64.b64decode(ciphertext)
    response = kms.decrypt(KeyId=key_ref, CiphertextBlob=ciphertext_blob)
    plaintext = response['Plaintext'].decode('utf-8')
    
    return {"plaintext": plaintext}, 200