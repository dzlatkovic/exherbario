import uvicorn
from fastapi import FastAPI

from app.db import Base
from app.db.database import engine

from app.field_loc.routes import field_loc_router
from app.photos.routes import photos_router
from app.publication.routes import publication_router, publication_authors_router
from app.specimen.routes import specimen_router, specimen_publication_router
from app.storage.routes import storage_router
from app.users.routes import user_router

Base.metadata.create_all(bind=engine)


def init_app():
    app = FastAPI()
    app.include_router(field_loc_router)
    app.include_router(photos_router)
    app.include_router(publication_authors_router)
    app.include_router(publication_router)
    app.include_router(specimen_publication_router)
    app.include_router(specimen_router)
    app.include_router(storage_router)
    app.include_router(user_router)
    return app


app = init_app()


@app.get("/", include_in_schema=False)
def hello_world():
    return {"message": "In Progress"}


if __name__ == "__main__":
    uvicorn.run(app)
