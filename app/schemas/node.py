from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.schemas._common import CommonPaginatedQuery


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


class UploadFile(BaseModel):
    name: str
    parent_id: int = None
    overwrite: bool = False


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
    name: str
    parent_id: int


class DeleteNode(BaseModel):
    recursive: bool = False
