import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from app.schemas.common import CommonPaginatedQuery
from app.schemas.node import ListNodesResponse, ListNode


class DisplayPermission(enum.StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    OWNER = "owner"


class Share(BaseModel):
    name: str | None = None
    user_id: UUID
    permission: DisplayPermission


class ShareNode(BaseModel):
    shares: list[Share]


class ListShares(CommonPaginatedQuery):
    """
    copy
    """


class ListSharesResponse(BaseModel):
    total: int
    shares: list[Share]


class ListSharedNodes(CommonPaginatedQuery):
    """
    copy
    """


class ListShareNode(ListNode):
    sharer_id: UUID
    shared_at: datetime


class ListSharedNodesResponse(BaseModel):
    total: int
    nodes: list[ListShareNode]
