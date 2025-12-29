from uuid import UUID

from fastapi import Path, HTTPException, status

def get_default_space_id(space_id: UUID | None = Path(None)):
    if space_id is not None:
        return space_id

    space_id = None
    if not space_id:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Space not found")

    return space_id