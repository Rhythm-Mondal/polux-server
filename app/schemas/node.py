from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class CreateSpace(BaseModel):
    name: str = Field(max_length=128)


class CreateNode(BaseModel):
    name: str = Field(max_length=128)
    parent_id: int = None
    space_id: UUID


class ListNodeChildrenIn(BaseModel):
    page: int = Field(None, gt=0)
    page_size: int = Field(None, gt=0)

    @computed_field
    @property
    def limit(self) -> int | None:
        if self.page is not None and self.page_size is None:
            return 10
        return self.page_size

    @computed_field
    @property
    def offset(self) -> int | None:
        if self.page_size is not None and self.page is None:
            return 0
        if self.page_size is not None:
            return (self.page - 1) * self.page_size
        return (self.page - 1) * 10


class ListNodes(BaseModel):
    id: int
    name: str
    type: str
    is_shared: bool = False
    owner_id: UUID
    uploader_id: UUID
    space_id: UUID
    parent_id: int | None = None
    status: str
    permission: str


class ListNodeChildrenOut(BaseModel):
    total_nodes: int = Field(0, ge=0)
    nodes: list[ListNodes] = Field(None)


class MoveNode(BaseModel):
    destination_id: int


class CopyNode(BaseModel):
    destination_id: int
    space_id: int = None


class ArchiveNode(BaseModel):
    pass


class RestoreNode(BaseModel):
    pass


class DeleteNode(BaseModel):
    pass
