"""Bearer authentication backed by the current user record."""

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from starlette.concurrency import run_in_threadpool

from app.users.models import User
from app.users.services import UserServices, decodeJWT


class JWTBearer(HTTPBearer):
    def __init__(self, role: str | None = None, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.role = role

    def make_not_authenticated_error(self) -> HTTPException:
        # HERBAR answers 403 for every authentication failure, including a missing token.
        return HTTPException(status_code=403, detail="Not authenticated")

    async def __call__(self, request: Request) -> User:
        credentials = await super().__call__(request)
        payload = decodeJWT(credentials.credentials) if credentials else None
        if not payload or not isinstance(payload.get("user_id"), str):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        user = await run_in_threadpool(UserServices.get_user_by_id, payload["user_id"])
        if not user or not user.is_active:
            raise HTTPException(status_code=403, detail="Account is unavailable.")
        current_role = "super_user" if user.is_superuser else "classic_user"
        if payload.get("role") != current_role or (self.role and current_role != self.role):
            raise HTTPException(status_code=403, detail="Account lacks the required role.")
        return user
