from marshmallow import Schema, fields


class AdminSchema(Schema):
    id = fields.Int(dump_only=True)
    login = fields.Str(required=True)
    password = fields.Str(required=True)


class LoginAdminSchema(Schema):
    login = fields.Str(required=True)
    password = fields.Str(required=True)


class ContestSchema(Schema):
    contest_id = fields.Int(dump_only=True)
    chat_id = fields.Int(required=True)
    creator_id = fields.Int(required=True)
    current_round = fields.Int(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    registration_deadline = fields.DateTime(dump_only=True)


class ContestsResponseSchema(Schema):
    contests = fields.List(fields.Nested(ContestSchema))


class UserSchema(Schema):
    user_id = fields.Int(required=True)


class DeleteContestSchema(Schema):
    contest_id = fields.Int(required=True)


class CreateUserSchema(Schema):
    user_id = fields.Int(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(allow_none=True)
    username = fields.Str(allow_none=True)
    photo_id = fields.Str(required=True)
