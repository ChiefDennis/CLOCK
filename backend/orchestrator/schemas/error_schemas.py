from marshmallow import Schema, fields

class ErrorSchema(Schema):
    """Schema for a generic API error response."""
    code = fields.Int(dump_only=True, metadata={"description": "The HTTP status code."})
    status = fields.Str(dump_only=True, metadata={"description": "The HTTP status name."})
    message = fields.Str(dump_only=True, metadata={"description": "A human-readable error message."})