from fastapi import FastAPI
from app.utils import database
from app.apis import auth

database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Polux")
app.include_router(auth.router)

