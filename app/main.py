from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.utils import auth, database

# models.Base.metadata.create_all(bind=database.engine)
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Polux")


@app.post("/register")
def register(user: schemas.user.UserCreate, db: Session = Depends(database.get_db)):
    if crud.user.get_user_by_email(db, email=str(user.email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    if not crud.user.create_user(db, user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to register user"
        )
    return {"message": "User registered"}


@app.post("/login")
def login(user: schemas.user.UserLogin, db: Session = Depends(database.get_db)):
    db_user = crud.user.get_user_by_email(db, email=str(user.email))
    if not db_user or not crud.user.verify_password(
        user.password.get_secret_value(), db_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    token = auth.create_access_token(
        {"user_id": str(db_user.id), "email": db_user.email, "name": db_user.name}
    )
    return {"access_token": token, "token_type": "bearer"}
