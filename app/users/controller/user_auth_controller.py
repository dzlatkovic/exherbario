"""
This module provides a FastAPI dependency to authenticate
and verify a JSON Web Token (JWT).
This is done by extending the `HTTPBearer` class and
verifying the JWT in the `__call__` method.
"""


from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.users.services import decodeJWT


class JWTBearer(HTTPBearer):
    """
    A FastAPI dependency for authenticating and verifying a JSON Web Token (JWT).
    :param role: The role required to access the resource protected by the JWT
    :param auto_error: Whether to raise an HTTPException if the verification fails
    """
    def __init__(self, role: str, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.role = role

    async def __call__(self, request: Request):
        """
        Verify the JSON Web Token (JWT) included in the request header
        If the verification succeeds, the method returns the token
        If the verification fails, an HTTPException is raised
        :param request: The request to be verified
        :return: The JSON Web Token included in the request header
        """
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            payload = self.verify_jwt(credentials.credentials)
            if not payload.get("valid"):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            if payload.get("role") != self.role:
                raise HTTPException(status_code=403, detail="User with provided role is not "
                                                            "permitted to access this route.")
            return credentials.credentials
        raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> dict:
        """
        Verify the JSON Web Token (JWT)
        This method calls the `decodeJWT` method to verify and decode the token
        :param jwtoken: The JSON Web Token to be verified.
        :return: A dictionary containing a boolean value indicating whether
        the verification was successful
        and the role associated with the token.
        """
        try:
            payload = decodeJWT(jwtoken)
        except Exception:
            payload = None
        return {"valid": bool(payload), "role": payload["role"] if payload else None}
