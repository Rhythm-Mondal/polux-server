from fastapi import FastAPI
from app.core import database
from app.apis import session, user, space, node, share, archive

database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Polux")
app.include_router(session.router)
app.include_router(user.router)
app.include_router(space.router)
app.include_router(node.router)
app.include_router(share.router)
app.include_router(archive.router)
