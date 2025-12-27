from pydantic import BaseModel, EmailStr, SecretStr


class UserLogin(BaseModel):
    email: EmailStr
    password: SecretStr
