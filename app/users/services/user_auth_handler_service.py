"""This module provides functions for generating and
decoding JSON Web Tokens (JWTs) for user authentication."""

import time
from typing import Dict

import jwt

from app.config import settings

USER_SECRET = settings.USER_SECRET
JWT_ALGORITHM = settings.ALGORITHM
TOKEN_DURATION = settings.TOKEN_DURATION


def signJWT(user_id: str, role: str) -> Dict[str, str]:
    """
    Sign a JWT for a user with the given user ID and role
    :param user_id: The ID of the user
    :type user_id: str
    :param role: The role of the user
    :type role: str
    :return: A dictionary with a single key "access_token"
    :rtype: dict
    """
    payload = {
        "user_id": user_id,
        "role": role,
        "expires": time.time() + TOKEN_DURATION
    }
    token = jwt.encode(payload, USER_SECRET, algorithm=JWT_ALGORITHM)

    return {"access_token": token}


def decodeJWT(token: str) -> dict:
    """
    Decode a JWT and return its payload if it is not expired
    :param token: A string representation of the JWT
    :type token: str
    :return: A dictionary representing the payload of the JWT if it is not expired,
             or an empty dictionary otherwise
    :rtype: dict
    """
    try:
        decoded_token = jwt.decode(token, USER_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}
