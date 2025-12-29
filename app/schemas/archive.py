from pydantic import BaseModel
from app.schemas.common import CommonPaginatedQuery
from app.schemas.node import Node


class ArchiveNodeCan(BaseModel):
    restore: bool = False
    delete: bool = False


class ArchiveNode(Node):
    can: ArchiveNodeCan


class ListArchive(CommonPaginatedQuery):
    node_id: int = None


class ListArchiveResponse(BaseModel):
    total: int
    nodes: list[ArchiveNode]


class RestoreNode(BaseModel):
    name: str = None
    overwrite: bool = None
