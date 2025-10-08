import hashlib
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import new_session

from app.web.app import View
from app.web.utils import json_response, error_json_response
from app.admin.schemes import AdminSchema
from app.web.schemes import OkResponseSchema
from app.web.middlewares import HTTP_ERROR_CODES

class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        email = self.data["email"]
        password = self.data["password"]

        admin = await self.store.admins.get_by_email(email)
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        if not admin or admin.password != hashed_password:
            return error_json_response(
                http_status=403,
                status=HTTP_ERROR_CODES[403],
                message="Invalid credentials"
            )
        
        session = await new_session(request=self.request)
        session["admin"] = {
            "id": admin.id,
            "email": admin.email,
        }

        return json_response(
            {"id": admin.id, "email": admin.email}
        )


class AdminCurrentView(View):
    async def get(self):
        admin = self.request["admin"] 
        return json_response(
            admin
        )
