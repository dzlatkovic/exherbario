from pydantic import BaseModel
from pydantic import UUID4, EmailStr


class UserSchema(BaseModel):
    user_id: UUID4
    name: str
    surname: str
    email: str
    password: str
    is_active: bool
    is_superuser: bool

    class Config:
        orm_mode = True


class UserSchemaIn(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str

    class Config:
        orm_mode = True


class UserSchemaLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True
