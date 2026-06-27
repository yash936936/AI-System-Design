"""
FastAPI authentication dependency.

Verifies the short-lived HS256 JWT that the Next.js bridge route
(/api/auth/backend-token) mints for each authenticated session.

Usage:
    from app.core.auth import get_current_user, UserClaims

    @router.get("/api/sessions")
    async def list_sessions(user: UserClaims = Depends(get_current_user)):
        ...  # user.user_id is the stable cross-provider user id
"""

import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

_ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def _get_secret() -> str:
    secret = os.getenv("INTERNAL_AUTH_SECRET", "dev-secret-change-me")
    return secret


class UserClaims:
    def __init__(self, user_id: str, email: str, name: str, provider: str):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.provider = provider

    def __repr__(self) -> str:
        return f"UserClaims(user_id={self.user_id!r}, provider={self.provider!r})"


def _decode_token(token: str) -> UserClaims:
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing 'sub' claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserClaims(
        user_id=user_id,
        email=payload.get("email", ""),
        name=payload.get("name", ""),
        provider=payload.get("provider", "unknown"),
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> UserClaims:
    """Strict — raises 401 if no valid token is present."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode_token(credentials.credentials)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[UserClaims]:
    """Lenient — returns None instead of raising when no token is present."""
    if credentials is None:
        return None
    try:
        return _decode_token(credentials.credentials)
    except HTTPException:
        return None