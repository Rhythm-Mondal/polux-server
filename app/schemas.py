from pydantic import BaseModel, EmailStr, SecretStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: SecretStr


class UserLogin(BaseModel):
    email: EmailStr
    password: SecretStr