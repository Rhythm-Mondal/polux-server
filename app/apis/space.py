from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.space import CreateSpace, ListSpacesResponse, ListSpaces, DeleteSpace
from app.schemas.user import UserSearchResponse
from app.utils import database

router = APIRouter(
    prefix="/spaces",
)


@router.post("/")
def create_space(request: CreateSpace, db: Session = Depends(database.get_session)):
    pass


@router.get("/", response_model=ListSpacesResponse)
def list_spaces(query: ListSpaces, db: Session = Depends(database.get_session)):
    pass


@router.patch("/{space_id}")
def rename_space(space_id: UUID, db: Session = Depends(database.get_session)):
    pass


@router.delete("/{space_id}")
def delete_space(
    space_id: UUID, query: DeleteSpace, db: Session = Depends(database.get_session)
):
    pass
