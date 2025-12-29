from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.schemas.common import AlphaNumSpaceStr, CommonPaginatedQuery


class Space(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class CreateSpace(BaseModel):
    name: AlphaNumSpaceStr = Field(min_length=3, max_length=128)


class ListSpaces(CommonPaginatedQuery):
    """
    copy
    """


class ListSpacesResponse(BaseModel):
    total: int
    spaces: list[Space]


class RenameSpace(BaseModel):
    name: AlphaNumSpaceStr = Field(min_length=3, max_length=128)


class DeleteSpace(BaseModel):
    delete_contents: bool = False
