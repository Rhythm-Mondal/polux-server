from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.logic.space import resolve_default_space_id
from app.schemas.node import (
    UploadFile,
    CreateFolder,
    GetNodeResponse,
    ListSpaceNodes,
    ListFolderNodes,
    CopyNode,
    MoveNode,
    DeleteNode,
    ListSpaceNodesResponse,
    ListFolderNodesResponse,
    RenameNode,
)
from app.utils import database

router = APIRouter(
    prefix="/spaces",
)


@router.post("/me/nodes/files")
@router.post("/{space_id}/nodes/files")
def upload_files(
    body: UploadFile,
    space_id: UUID = Depends(resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.post("/me/nodes/files")
@router.post("/{space_id}/nodes/files")
def create_folder(
    body: CreateFolder,
    space_id: UUID = Depends(resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.get("/me/nodes/{node_id}", response_model=GetNodeResponse)
@router.get("/{space_id}/nodes/{node_id}", response_model=GetNodeResponse)
def get_node_metadata(
    node_id: int,
    space_id: UUID = Depends(resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.get("/me/nodes", response_model=ListSpaceNodesResponse)
@router.get("/{space_id}/nodes", response_model=ListSpaceNodesResponse)
def list_space_nodes(
    space_id: UUID = Depends(resolve_default_space_id),
    query: ListSpaceNodes = Depends(),
    db: Session = Depends(database.get_session),
):
    pass


@router.get("/me/nodes/{node_id}/list", response_model=ListFolderNodesResponse)
@router.get("/{space_id}/nodes/{node_id}/list", response_model=ListFolderNodesResponse)
def list_folder_nodes(
    node_id: int,
    space_id: UUID = Depends(resolve_default_space_id),
    query: ListFolderNodes = Depends(database.get_session),
    db: Session = Depends(database.get_session),
):
    pass


@router.patch("/me/nodes/{node_id}")
@router.patch("/{space_id}/nodes/{node_id}")
def rename_node(
    body: RenameNode,
    node_id: int,
    space_id: UUID = Depends(resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.put("/me/nodes/{node_id}/copy")
@router.patch("/{space_id}/nodes/{node_id}")
def copy_node(
    node_id: int,
    body: CopyNode,
    space_id: UUID = Depends(resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.put("/me/nodes/{node_id}/move")
@router.put("/{space_id}/nodes/{node_id}/move")
def move_node(
    node_id: int,
    body: MoveNode,
    space_id: UUID = Depends(resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.patch("/me/nodes/{node_id}/archive")
@router.patch("/{space_id}/nodes/{node_id}/archive")
def archive_node(
    node_id: int,
    space_id: UUID = Depends(resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.delete("/me/nodes/{node_id}")
@router.delete("/{space_id}/nodes/{node_id}")
def delete_node(
    node_id: int,
    space_id: UUID = Depends(resolve_default_space_id),
    query: DeleteNode = Depends(),
    db: Session = Depends(database.get_session),
):
    pass
