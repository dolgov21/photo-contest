from pydantic import BaseModel, Field


class OkResponseSchema(BaseModel):
    status: int
    data: str
