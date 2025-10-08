from pydantic import BaseModel, Field


class Admin(BaseModel):
    id: int = Field(exclude=True, hidden_from_schema=True)
    email: str
    password: str
