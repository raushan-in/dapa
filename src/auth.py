"""
This module provides authentication functionalities using FastAPI.
It includes functions to verify bearer tokens and handle authorization.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.settings import settings


def verify_bearer(
    http_auth: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(
            HTTPBearer(
                description="Please provide AUTH_SECRET api key.", auto_error=False
            )
        ),
    ],
) -> None:
    """
    Verifies the provided bearer token against the AUTH_SECRET setting.

    Parameters:
    - http_auth: The HTTP authorization credentials provided by the client.

    Raises:
    - HTTPException: If the token is invalid or not provided.
    """
    if not settings.AUTH_SECRET:
        return
    auth_secret = settings.AUTH_SECRET.get_secret_value()
    if not http_auth or http_auth.credentials != auth_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
