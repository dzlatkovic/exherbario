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

from app.catalog_routes import router as catalog_router
from app.chemistry.controller import chemistry_error_response
from app.chemistry.exceptions import ChemistryError
from app.chemistry.routes import chemistry_router
from app.config import settings

from app.field_loc.routes import field_loc_router
from app.publication.routes import publication_router, publication_authors_router
from app.specimen.routes import specimen_router, specimen_publication_router, revision_router
from app.storage.routes import storage_router
from app.users.routes import user_router
from app.weather.routes import weather_router
from app.image.routes import image_router, plantnet_router
from app.taxonomy.routes import taxonomy_router

def init_app():
    """
    Initializes the FastAPI application and includes all the necessary routers.

    This function creates a new instance of the FastAPI app,
    includes all the routers for the different endpoints,
    and returns the app instance.
    :return: FastAPI app instance with all the routers included.
    """
    fastapi_app = FastAPI()
    fastapi_app.add_exception_handler(ChemistryError, chemistry_error_response)

    @fastapi_app.on_event("startup")
    def validate_auth_config():
        if len(settings.USER_SECRET.encode()) < 32:
            raise RuntimeError("Set USER_SECRET to a random value of at least 32 bytes.")

    fastapi_app.include_router(field_loc_router)
    fastapi_app.include_router(image_router)
    fastapi_app.include_router(plantnet_router)
    fastapi_app.include_router(publication_authors_router)
    fastapi_app.include_router(publication_router)
    fastapi_app.include_router(revision_router)
    fastapi_app.include_router(specimen_publication_router)
    fastapi_app.include_router(specimen_router)
    fastapi_app.include_router(storage_router)
    fastapi_app.include_router(taxonomy_router)
    fastapi_app.include_router(user_router)
    fastapi_app.include_router(weather_router)
    fastapi_app.include_router(chemistry_router)
    fastapi_app.include_router(catalog_router)
    return fastapi_app


app = init_app()


@app.get("/", include_in_schema=False)
def hello_world():
    return {"message": "In Progress"}


if __name__ == "__main__":
    uvicorn.run(app)
