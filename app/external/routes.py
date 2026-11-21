from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.external.lookups import LookupUnavailable, provider_status
from app.users.controller import JWTBearer

external_router = APIRouter(prefix="/api/external", tags=["External lookups"])


@external_router.get("/providers", dependencies=[Depends(JWTBearer("super_user"))])
def providers():
    """The registries curators can query on this instance, with the attribution their data carries."""
    return provider_status()


def lookup_unavailable_response(_request, error: LookupUnavailable):
    return JSONResponse(status_code=error.code, content={"detail": error.message, "provider": error.provider})
