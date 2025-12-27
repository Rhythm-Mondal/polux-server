from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, SecretStr, computed_field


class User(BaseModel):
    id: UUID
    name: str
    email: EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: SecretStr


class UserSearch(BaseModel):
    text: str = Field(None, min_length=3, max_length=256)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1)

    @computed_field
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @computed_field
    @property
    def limit(self) -> int:
        return self.page_size

    @computed_field
    @property
    def search_tokens(self) -> list[str]:
        if not self.text:
            return []

        return list(map(str.strip, self.text.split(" ")))


class UserSearchResponse(BaseModel):
    total: int
    users: list[User]
