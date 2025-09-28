from marshmallow import Schema, fields

class ModuleStatusSchema(Schema):
    provider_name = fields.Str(dump_only=True)
    is_enabled = fields.Boolean(required=True)
    last_synced_at = fields.DateTime(dump_only=True, allow_none=True)