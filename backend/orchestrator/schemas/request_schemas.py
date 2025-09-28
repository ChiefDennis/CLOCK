# /orchestrator/schemas/request_schemas.py

from marshmallow import Schema, fields, validate, EXCLUDE


# ---------- Auth ----------

class LoginSchema(Schema):
    username = fields.Str(required=True, metadata={"description": "Username"})
    password = fields.Str(required=True, metadata={"description": "Password"})


# ---------- Common base ----------

class _ProviderSchema(Schema):
    class Meta:
        unknown = EXCLUDE  # ignore extra client fields

    cloud_provider = fields.Str(
        required=True,
        validate=validate.OneOf(["aws", "azure", "gcp"]),
        metadata={"description": "Target cloud provider"}
    )


# ---------- Endpoint-specific ----------

class CreateKeySchema(_ProviderSchema):
    # Vendor-agnostic inputs for symmetric keys
    algorithm = fields.Str(
        required=False,
        validate=validate.OneOf(["AES_256"]),
        metadata={"description": "Key algorithm (symmetric only). Default AES_256"}
    )
    purpose = fields.Str(
        required=False,
        validate=validate.OneOf(["ENCRYPT_DECRYPT"]),
        metadata={"description": "Key purpose. Default ENCRYPT_DECRYPT"}
    )
    protection_level = fields.Str(
        required=False,
        validate=validate.OneOf(["HSM", "SOFTWARE"]),
        metadata={"description": "Where key material resides"}
    )
    description = fields.Str(required=False, metadata={"description": "Human-readable description"})
    labels = fields.Dict(keys=fields.Str(), values=fields.Str(), required=False,
                         metadata={"description": "Tags/labels"})
    rotation_enabled = fields.Boolean(required=False, metadata={"description": "Enable automatic rotation"})
    rotation_days = fields.Int(required=False, validate=validate.Range(min=1, max=3650),
                               metadata={"description": "Rotation period in days (provider-dependent)"})


class GetKeySchema(_ProviderSchema):
    key_id = fields.Str(required=True, metadata={
        "description": "Provider key resource (AWS ARN | Azure key URL | GCP CryptoKey name)"
    })


class ListKeysQuerySchema(_ProviderSchema):
    page_size = fields.Int(required=False, validate=validate.Range(min=1, max=1000),
                           metadata={"description": "Items per page"})
    page_token = fields.Str(required=False, metadata={"description": "Opaque pagination token"})


class SetEnabledSchema(_ProviderSchema):
    key_id = fields.Str(required=True, metadata={"description": "Key resource (no version)"})
    enabled = fields.Boolean(required=True, metadata={"description": "Enable (true) or disable (false)"})


class SetRotationSchema(_ProviderSchema):
    key_id = fields.Str(required=True, metadata={"description": "Key resource (no version)"})
    enabled = fields.Boolean(required=True, metadata={"description": "Turn rotation on/off"})
    rotation_days = fields.Int(required=False, validate=validate.Range(min=1, max=3650),
                               metadata={"description": "Rotation period in days (provider-dependent)"})

class DeleteKeySchema(_ProviderSchema):
    """Schema for deleting a key, requires a schedule."""
    key_id = fields.Str(required=True, metadata={"description": "Key resource (no version)"})
    schedule_days = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=3650),
        metadata={"description": "Pending window (provider-dependent; AWS clamps 7–30)"}
    )

class EncryptSchema(_ProviderSchema):
    key_id = fields.Str(required=True, metadata={"description": "Provider key resource (AWS ARN | ...)"})
    plaintext = fields.Str(required=True, metadata={"description": "The data to be encrypted."})

class EncryptResponseSchema(Schema):
    ciphertext = fields.Str(metadata={"description": "The base64-encoded encrypted data."})

class DecryptSchema(_ProviderSchema):
    key_id = fields.Str(required=True, metadata={"description": "Provider key resource (AWS ARN | ...)"})
    ciphertext = fields.Str(required=True, metadata={"description": "The base64-encoded data to be decrypted."})

class DecryptResponseSchema(Schema):
    plaintext = fields.Str(metadata={"description": "The decrypted plaintext data."})
class EncryptSchema(_ProviderSchema):
    key_id = fields.Str(required=True, metadata={"description": "Provider key resource (AWS ARN | ...)"})
    plaintext = fields.Str(required=True, metadata={"description": "The data to be encrypted."})

class EncryptResponseSchema(Schema):
    ciphertext = fields.Str(metadata={"description": "The base64-encoded encrypted data."})

class DecryptSchema(_ProviderSchema):
    key_id = fields.Str(required=True, metadata={"description": "Provider key resource (AWS ARN | ...)"})
    ciphertext = fields.Str(required=True, metadata={"description": "The base64-encoded data to be decrypted."})

class DecryptResponseSchema(Schema):
    plaintext = fields.Str(metadata={"description": "The decrypted plaintext data."})

# ---------- Other ----------

class ListLocalKeysQuerySchema(Schema):
    """Defines the query parameters for listing locally stored keys."""
    cloud_provider = fields.Str(
        required=False,
        validate=validate.OneOf(["aws", "azure", "gcp"]),
        metadata={"description": "Filter by cloud provider."}
    )
    region = fields.Str(
        required=False,
        metadata={"description": "Filter by region."}
    )
    status = fields.Str(
        required=False,
        validate=validate.OneOf(["Enabled", "Disabled"]),
        metadata={"description": "Filter by key status."}
    )
    rotation_enabled = fields.Boolean(
        required=False,
        metadata={"description": "Filter by rotation status."}
    )

class SyncSchema(Schema):
    cloud_provider = fields.Str(
        required=True,
        validate=validate.OneOf(["aws", "azure", "gcp"]),
        metadata={"description": "The cloud provider to synchronize with."}
    )

class SyncSummarySchema(Schema):
    provider = fields.Str()
    status = fields.Str()
    summary = fields.Dict(keys=fields.Str(), values=fields.Int())

class PendingActionSchema(Schema):
    id = fields.Int()
    action_type = fields.Str()
    resource_id = fields.Str(attribute="resource_identifier")
    created_by = fields.Str(attribute="created_by_username")
    created_at = fields.DateTime()
    expires_at = fields.DateTime()
    status = fields.Str()
    reviewed_by = fields.Str(attribute="reviewed_by_username", allow_none=True)
    reviewed_at = fields.DateTime(allow_none=True)


class TokenSchema(Schema):
    access_token = fields.Str(required=True, metadata={"description": "A JWT access token."})

class MessageSchema(Schema):
    message = fields.Str()
    action_id = fields.Int(required=False)

# ------------- Log-related schemas ----------

class LogSchema(Schema):
    """Schema for a single log entry."""
    id = fields.Int(dump_only=True)
    username = fields.Str()
    role = fields.Str()
    method = fields.Str()
    endpoint = fields.Str()
    status_code = fields.Int()
    request_data = fields.Str()
    response_data = fields.Str()
    action = fields.Str()
    timestamp = fields.DateTime(dump_only=True)

class LogQuerySchema(Schema):
    """Schema for log query parameters."""
    page_size = fields.Int(
        required=False, 
        validate=validate.Range(min=1, max=100),
        load_default=50, # Default page size if not provided
        metadata={"description": "Number of log entries per page."}
    )
    # The 'token' is the ID of the last log entry from the previous page.
    page_token = fields.Int(
        required=False,
        metadata={"description": "The ID of the last log entry from the previous page to fetch the next set."}
    )

class PaginatedLogResponseSchema(Schema):
    """Schema for the paginated log response."""
    logs = fields.List(fields.Nested(LogSchema))
    # The next token to use in the subsequent request to get the next page.
    next_page_token = fields.Int(
        allow_none=True, 
        metadata={"description": "Token to fetch the next page. Null if no more pages."}
    )

# --- Alarm schemas ---

class AlarmSchema(Schema):
    """Schema for a single alarm entry."""
    id = fields.Int(dump_only=True)
    timestamp = fields.DateTime(dump_only=True)
    severity = fields.Str()
    event_type = fields.Str()
    message = fields.Str()
    is_acknowledged = fields.Boolean()

class AlarmQuerySchema(Schema):
    """Schema for alarm query parameters."""
    page_size = fields.Int(
        required=False,
        load_default=50, # Use load_default for Marshmallow 3+
        validate=validate.Range(min=1, max=100),
        metadata={"description": "Number of alarm entries per page."}
    )
    page_token = fields.Int(
        required=False,
        metadata={"description": "The ID of the last alarm from the previous page."}
    )

class PaginatedAlarmResponseSchema(Schema):
    """Schema for the paginated alarm response."""
    alarms = fields.List(fields.Nested(AlarmSchema))
    next_page_token = fields.Int(
        allow_none=True,
        metadata={"description": "Token to fetch the next page. Null if no more pages."}
    )