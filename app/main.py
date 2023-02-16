"""
HERBAR is an online platform that offers significant advantages over
non-digital herbariums, including faster and easier access to the data,
automated statistical analysis, increased public accessibility to the
collection, and the ability for researchers to access the Herbarium
from the field through their mobile devices.

For more information on how to use this application,
please refer to the documentation.
"""


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
    """
    Initializes the FastAPI application and includes all the necessary routers.

    This function creates a new instance of the FastAPI app,
    includes all the routers for the different endpoints,
    and returns the app instance.
    :return: FastAPI app instance with all the routers included.
    """
    fastapi_app = FastAPI()
    fastapi_app.include_router(field_loc_router)
    fastapi_app.include_router(photos_router)
    fastapi_app.include_router(publication_authors_router)
    fastapi_app.include_router(publication_router)
    fastapi_app.include_router(specimen_publication_router)
    fastapi_app.include_router(specimen_router)
    fastapi_app.include_router(storage_router)
    fastapi_app.include_router(user_router)
    return fastapi_app


app = init_app()


@app.get("/", include_in_schema=False)
def hello_world():
    """
    `hello_world` returns a dictionary with a key of `message` and a value of `In Progress`
    :return: A dictionary with a key of message and a value of In Progress
    """
    return {"message": "In Progress"}


if __name__ == "__main__":
    uvicorn.run(app)
