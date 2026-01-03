from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from app.core.constant import ALLOWED_MIME_TYPES, MIME_ALIASES
from app.schemas.common import CommonPaginatedQuery


class Node(BaseModel):
    id: int
    parent_id: int | None = None
    space_id: UUID
    type: str
    name: str
    uploader_id: UUID
    created_at: datetime
    updated_at: datetime
    is_shared: bool


class ListNodeCan(BaseModel):
    open: bool = False
    upload: bool = False
    download: bool = False
    rename: bool = False
    copy: bool = False
    cut: bool = False
    paste: bool = False
    archive: bool = False
    delete: bool = False
    share: bool = False


class ListNode(Node):
    can: ListNodeCan


class CreateFile(BaseModel):
    name: str
    parent_id: int = None
    overwrite: bool = False
    mime_type: str = None
    size_bytes: int = Field(None, gt=0)

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, value: str):
        value = value.strip().lower()
        if MIME_ALIASES.get(value, value) not in ALLOWED_MIME_TYPES:
            raise PydanticCustomError("value error", "Invalid / Disallowed mimetype")
        return value


class CreateFolder(BaseModel):
    name: str
    parent_id: int = None


class GetNodeResponse(Node):
    """
    Some file specific optional values go here
    """


class ListNodesResponse(BaseModel):
    total: int
    nodes: list[ListNode]


class ListSpaceNodes(CommonPaginatedQuery):
    """
    copy
    """


class ListSpaceNodesResponse(ListNodesResponse):
    """
    copy
    """


class ListFolderNodes(CommonPaginatedQuery):
    """
    copy
    """


class ListFolderNodesResponse(ListNodesResponse):
    """
    copy
    """


class RenameNode(BaseModel):
    name: str


class CopyNode(BaseModel):
    name: str = None
    parent_id: int = None
    space_id: UUID


class MoveNode(BaseModel):
    name: str = None
    parent_id: int = None


class DeleteNode(BaseModel):
    recursive: bool = False
