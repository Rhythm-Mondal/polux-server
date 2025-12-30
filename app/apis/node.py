from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.logic.node import (
    logic_user_satisfies_permission,
    logic_create_folder,
    logic_list_space_nodes,
    logic_count_listed_space_nodes, logic_list_folder_nodes, logic_count_listed_folder_nodes,
)
from app.logic.space import logic_resolve_default_space_id
from app.models.node import SharePermission
from app.schemas.common import Token
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
from app.utils.auth import get_auth_user

router = APIRouter(
    prefix="/spaces",
)


@router.post("/me/nodes/files")
@router.post("/{space_id}/nodes/files")
def upload_files(
    body: UploadFile,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.post("/me/nodes/folders")
@router.post("/{space_id}/nodes/folders")
def create_folder(
    body: CreateFolder,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    if not logic_user_satisfies_permission(
        db, user.user_id, space_id, body.parent_id, SharePermission.WRITE
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Can not create folder here"
        )

    if not logic_create_folder(db, user.user_id, space_id, body):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create folder"
        )

    return {"message": "Folder created successfully"}


@router.get("/me/nodes/{node_id}", response_model=GetNodeResponse)
@router.get("/{space_id}/nodes/{node_id}", response_model=GetNodeResponse)
def get_node_metadata(
    node_id: int,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    pass


@router.get("/me/nodes", response_model=ListSpaceNodesResponse)
@router.get("/{space_id}/nodes", response_model=ListSpaceNodesResponse)
def list_space_nodes(
    space_id: UUID = Depends(logic_resolve_default_space_id),
    query: ListSpaceNodes = Depends(),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    if not logic_user_satisfies_permission(
        db, user.user_id, space_id, permission=SharePermission.READ
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Space not found"
        )

    nodes = logic_list_space_nodes(db, space_id, query)
    total = logic_count_listed_space_nodes(db, space_id)
    return {"nodes": nodes, "total": total}


@router.get("/me/nodes/{node_id}/list", response_model=ListFolderNodesResponse)
@router.get("/{space_id}/nodes/{node_id}/list", response_model=ListFolderNodesResponse)
def list_folder_nodes(
    node_id: int,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    query: ListFolderNodes = Depends(),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    if not logic_user_satisfies_permission(
            db, user.user_id, space_id, node_id, permission=SharePermission.READ
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Space not found"
        )

    nodes = logic_list_folder_nodes(db, space_id, node_id, query)
    total = logic_count_listed_folder_nodes(db, space_id, node_id)
    return {"nodes": nodes, "total": total}


@router.patch("/me/nodes/{node_id}")
@router.patch("/{space_id}/nodes/{node_id}")
def rename_node(
    body: RenameNode,
    node_id: int,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.put("/me/nodes/{node_id}/copy")
@router.patch("/{space_id}/nodes/{node_id}")
def copy_node(
    node_id: int,
    body: CopyNode,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.put("/me/nodes/{node_id}/move")
@router.put("/{space_id}/nodes/{node_id}/move")
def move_node(
    node_id: int,
    body: MoveNode,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    db: Session = Depends(database.get_session),
):
    pass


@router.patch("/me/nodes/{node_id}/archive")
@router.patch("/{space_id}/nodes/{node_id}/archive")
def archive_node(
    node_id: int,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    pass


@router.delete("/me/nodes/{node_id}")
@router.delete("/{space_id}/nodes/{node_id}")
def delete_node(
    node_id: int,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    query: DeleteNode = Depends(),
    db: Session = Depends(database.get_session),
):
    pass
