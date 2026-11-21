"""Bearer authentication backed by the current user record.

Browsers may authenticate with the session cookie instead; unsafe requests then need the CSRF header.
"""

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from starlette.concurrency import run_in_threadpool

from app.users.models import User
from app.users.services import UserServices, decodeJWT
from app.users.session import SAFE_METHODS, SESSION_COOKIE, csrf_valid


class JWTBearer(HTTPBearer):
    def __init__(self, role: str | None = None, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.role = role

    def make_not_authenticated_error(self) -> HTTPException:
        # HERBAR answers 403 for every authentication failure, including a missing token.
        return HTTPException(status_code=403, detail="Not authenticated")

    async def __call__(self, request: Request) -> User:
        if request.headers.get("Authorization") or not request.cookies.get(SESSION_COOKIE):
            credentials = await super().__call__(request)
            token = credentials.credentials if credentials else None
        else:
            token = request.cookies[SESSION_COOKIE]
            if request.method not in SAFE_METHODS and not csrf_valid(request):
                raise HTTPException(status_code=403, detail="Missing or invalid CSRF token. Reload the page.")
        payload = decodeJWT(token) if token else None
        if not payload or not isinstance(payload.get("user_id"), str):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        user = await run_in_threadpool(UserServices.get_user_by_id, payload["user_id"])
        if not user or not user.is_active:
            raise HTTPException(status_code=403, detail="Account is unavailable.")
        current_role = "super_user" if user.is_superuser else "classic_user"
        if payload.get("role") != current_role or (self.role and current_role != self.role):
            raise HTTPException(status_code=403, detail="Account lacks the required role.")
        return user
