from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(["user", "admin"]))
    enabled = fields.Boolean(dump_only=True) # dump_only includes it in responses

class UserCreateSchema(UserSchema):
    password = fields.Str(required=True, load_only=True)

class UserUpdateSchema(Schema):
    """Schema for updating a user. All fields are optional."""
    username = fields.Str()
    password = fields.Str(load_only=True)
    role = fields.Str(validate=validate.OneOf(["user", "admin"]))
    enabled = fields.Boolean()