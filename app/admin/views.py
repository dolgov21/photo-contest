import hashlib

from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import new_session

from app.admin.schemes import (
    ContestsResponseSchema,
    CreateUserSchema,
    LoginAdminSchema,
)
from app.web.app import View
from app.web.mw import HTTP_ERROR_CODES
from app.web.schemes import OkResponseSchema
from app.web.utils import error_json_response, json_response


class AdminLoginView(View):
    @docs(tags=["admin"], summary="Admin login")
    @request_schema(LoginAdminSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        login = self.data["login"]
        password = self.data["password"]

        admin = await self.store.admin.get_admin_by_login(login)
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        if not admin or admin.password != hashed_password:
            return error_json_response(
                http_status=403,
                status=HTTP_ERROR_CODES[403],
                message="Invalid credentials",
            )

        session = await new_session(request=self.request)
        session["admin"] = {
            "id": admin.id,
            "login": admin.login,
        }

        return json_response({"id": admin.id, "login": admin.login})


class AdminCurrentView(View):
    @docs(tags=["admin"], summary="Get current admin")
    @response_schema(OkResponseSchema, 200)
    async def get(self):
        admin = self.request.get("admin")

        if not admin:
            return error_json_response(
                http_status=401,
                status=HTTP_ERROR_CODES[401],
                message="Not authenticated",
            )

        return json_response(admin)


class AdminContestsView(View):
    @docs(tags=["admin"], summary="Get all contests")
    @response_schema(ContestsResponseSchema, 200)
    async def get(self):
        contests = await self.store.admin.get_all_contests()
        return json_response(
            {
                "contests": [
                    {
                        "contest_id": c.contest_id,
                        "chat_id": c.chat_id,
                        "current_round": c.current_round,
                        "is_active": c.is_active,
                        "registration_deadline": 
                            c.registration_deadline.isoformat()
                        if c.registration_deadline
                        else None,
                        "creator_id": c.creator_id,
                    }
                    for c in contests
                ]
            }
        )


class AdminCreateUserView(View):
    @request_schema(CreateUserSchema)
    @response_schema(OkResponseSchema, 200)
    @docs(tags=["admin"], summary="Add user to db")
    async def post(self):
        user = await self.store.admin.create_user(
            user_id=self.data["user_id"],
            first_name=self.data["first_name"],
            last_name=self.data.get("last_name"),
            username=self.data.get("username"),
            photo_id=self.data.get("photo_id"),
        )

        if not user:
            return error_json_response(
                http_status=400,
                status=HTTP_ERROR_CODES[400],
                message="Failed user create",
            )

        return json_response({"creates_user_id": user.user_id})


class AdminDeleteContestView(View):
    @docs(tags=["admin"], summary="Delete contest by ID")
    @response_schema(OkResponseSchema, 200)
    async def delete(self):
        contest_id = int(self.request.match_info["contest_id"])
        contest = await self.store.admin.get_contest_by_id(contest_id)

        if not contest:
            return error_json_response(
                http_status=404,
                status=HTTP_ERROR_CODES[404],
                message="Contest not found",
            )

        success = await self.store.admin.delete_contest(contest_id)

        if not success:
            return error_json_response(
                http_status=500,
                status=HTTP_ERROR_CODES[500],
                message="Failed to delete contest",
            )

        return json_response({"status": "deleted"})
