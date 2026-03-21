from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class ClientCreate(BaseModel):
    name: str
    email: EmailStr

class ClientUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None

class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime