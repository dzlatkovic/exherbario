"""
Ex Herbario (formerly HERBAR) is an online platform that offers significant advantages over
non-digital herbariums, including faster and easier access to the data,
automated statistical analysis, increased public accessibility to the
collection, and the ability for researchers to access the Herbarium
from the field through their mobile devices.

For more information on how to use this application,
please refer to the documentation.
"""

import asyncio

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.catalog_routes import router as catalog_router
from app.chemistry.controller import chemistry_error_response
from app.chemistry.exceptions import ChemistryError
from app.chemistry.routes import chemistry_router
from app import site_lock
from app.config import settings
from app.deposition.routes import institution_router, router as deposition_router
from app.external.lookups import LookupUnavailable
from app.external.routes import external_router, lookup_unavailable_response

from app.field_loc.routes import field_loc_router
from app.publication.routes import publication_router, publication_authors_router
from app.specimen.routes import specimen_router, specimen_publication_router, revision_router
from app.storage.routes import storage_router
from app.users.routes import user_router
from app.weather.routes import weather_router
from app.image.routes import image_router, plantnet_router
from app.taxonomy.routes import taxonomy_router
from app.visibility_routes import router as visibility_router
from app.web.routes import ROOT as WEB_ROOT, router as web_router

def validate_auth_config():
    if len(settings.USER_SECRET.encode()) < 32:
        raise RuntimeError("Set USER_SECRET to a random value of at least 32 bytes.")


def init_app():
    """
    Initializes the FastAPI application and includes all the necessary routers.

    This function creates a new instance of the FastAPI app,
    includes all the routers for the different endpoints,
    and returns the app instance.
    :return: FastAPI app instance with all the routers included.
    """
    @asynccontextmanager
    async def lifespan(_app):
        validate_auth_config()
        nightly = None
        if settings.DEMO_MODE and 0 <= settings.DEMO_RESET_HOUR <= 23:
            from app.demo import nightly_reset
            nightly = asyncio.create_task(nightly_reset(settings.DEMO_RESET_HOUR))
        yield
        if nightly is not None:
            nightly.cancel()

    fastapi_app = FastAPI(title="Ex Herbario", lifespan=lifespan,
                          description="Voucher-linked herbarium records and citable scientific depositions.")
    fastapi_app.add_exception_handler(ChemistryError, chemistry_error_response)
    fastapi_app.add_exception_handler(LookupUnavailable, lookup_unavailable_response)

    @fastapi_app.middleware("http")
    async def prevent_record_caching(request: Request, call_next):
        if not site_lock.unlocked(request):
            return site_lock.locked_response(request)
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if settings.DEMO_MODE:
            # Synthetic demo records must not reach search engines or be mistaken for real ones.
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

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
    fastapi_app.include_router(deposition_router)
    fastapi_app.include_router(external_router)
    fastapi_app.include_router(institution_router)
    fastapi_app.include_router(visibility_router)
    fastapi_app.include_router(catalog_router)
    fastapi_app.include_router(web_router)
    fastapi_app.mount("/assets/herbar", StaticFiles(directory=WEB_ROOT / "assets"), name="herbar-assets")
    return fastapi_app


app = init_app()


if __name__ == "__main__":
    uvicorn.run(app)
