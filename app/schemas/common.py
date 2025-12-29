from uuid import UUID
from typing import Annotated

from pydantic import BaseModel, Field, EmailStr, StringConstraints, computed_field


AlphaNumSpaceStr = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[a-zA-Z0-9 ]+$")
]


class Token(BaseModel):
    space_id: UUID
    user_id: UUID
    email: EmailStr
    exp: float | None = None


class CommonPaginatedQuery(BaseModel):
    page: int | None = Field(None, ge=1)
    page_size: int | None = Field(None, ge=0)

    @computed_field
    @property
    def offset(self) -> int | None:
        if self.page is None and self.page_size is not None:
            return 0
        if self.page_size is not None:
            return (self.page - 1) * self.page_size
        return self.page

    @computed_field
    @property
    def limit(self) -> int | None:
        if self.page_size is None and self.page is not None:
            return 10
        return self.page_size
