from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
)
from app.utils import database

router = APIRouter(
    prefix="/spaces",
)


@router.post("/me/nodes/files")
def upload_files_default(body: UploadFile, db: Session = Depends(database.get_db)):
    pass


@router.post("/{space_id}/nodes/files")
def upload_files(
    space_id: UUID, body: UploadFile, db: Session = Depends(database.get_db)
):
    pass


@router.post("/me/nodes/files")
def create_folder_default(body: CreateFolder, db: Session = Depends(database.get_db)):
    pass


@router.post("/{space_id}/nodes/files")
def create_folder(
    space_id: UUID, body: CreateFolder, db: Session = Depends(database.get_db)
):
    pass


@router.get("/me/nodes/{node_id}", response_model=GetNodeResponse)
def get_node_metadata_default(node_id: int, db: Session = Depends(database.get_db)):
    pass


@router.get("/{space_id}/nodes/{node_id}", response_model=GetNodeResponse)
def get_node_metadata(
    space_id: UUID, node_id: int, db: Session = Depends(database.get_db)
):
    pass


@router.get("/me/nodes", response_model=ListSpaceNodesResponse)
def list_space_nodes_default(
    query: ListSpaceNodes, db: Session = Depends(database.get_db)
):
    pass


@router.get("/{space_id}/nodes", response_model=ListSpaceNodesResponse)
def list_space_nodes(
    space_id: UUID, query: ListSpaceNodes, db: Session = Depends(database.get_db)
):
    pass


@router.get("/me/nodes/{node_id}/list", response_model=ListFolderNodesResponse)
def list_folder_nodes_default(
    node_id: int, query: ListFolderNodes, db: Session = Depends(database.get_db)
):
    pass


@router.get("/{space_id}/nodes/{node_id}/list", response_model=ListFolderNodesResponse)
def list_folder_nodes(
    space_id: UUID,
    node_id: int,
    query: ListFolderNodes,
    db: Session = Depends(database.get_db),
):
    pass


@router.patch("/me/nodes/{node_id}")
def rename_node_default(node_id: int, db: Session = Depends(database.get_db)):
    pass


@router.patch("/{space_id}/nodes/{node_id}")
def rename_node(space_id: UUID, node_id: int, db: Session = Depends(database.get_db)):
    pass


@router.put("/me/nodes/{node_id}/copy")
def copy_node_default(
    node_id: int, body: CopyNode, db: Session = Depends(database.get_db)
):
    pass


@router.patch("/{space_id}/nodes/{node_id}")
def copy_node(
    space_id: UUID, node_id: int, body: CopyNode, db: Session = Depends(database.get_db)
):
    pass


@router.put("/me/nodes/{node_id}/move")
def move_node_default(
    node_id: int, body: MoveNode, db: Session = Depends(database.get_db)
):
    pass


@router.put("/{space_id}/nodes/{node_id}/move")
def move_node(
    space_id: UUID, node_id: int, body: MoveNode, db: Session = Depends(database.get_db)
):
    pass


@router.patch("/me/nodes/{node_id}/archive")
def archive_node_default(node_id: int, db: Session = Depends(database.get_db)):
    pass


@router.patch("/{space_id}/nodes/{node_id}/archive")
def archive_node(space_id: UUID, node_id: int, db: Session = Depends(database.get_db)):
    pass


@router.delete("/me/nodes/{node_id}")
def delete_node_default(
    node_id: int, query: DeleteNode, db: Session = Depends(database.get_db)
):
    pass


@router.delete("/{space_id}/nodes/{node_id}")
def delete_node(
    space_id: UUID,
    node_id: int,
    query: DeleteNode,
    db: Session = Depends(database.get_db),
):
    pass
