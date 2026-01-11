"""Security utilities for JWT validation."""
from typing import Dict, Any
from uuid import UUID
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# Bearer scheme for dependency injection
http_bearer = HTTPBearer(auto_error=True)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT access token using HS256."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> UUID:
    """Extract current user ID from JWT bearer token."""
    payload = decode_access_token(credentials.credentials)
    return UUID(str(payload.get("sub")))
