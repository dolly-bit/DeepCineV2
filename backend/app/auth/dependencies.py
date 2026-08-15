from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.auth.jwt_handler import decode_access_token

# auto_error=False so a missing header raises our own clear 401 (and
# gets caught by the frontend's response interceptor) instead of a
# generic FastAPI security error.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(credentials.credentials)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        # Token is well-formed but the user it points to no longer
        # exists (e.g. a fresh/reset local database) - same 401 signal,
        # so the frontend clears the stale session automatically.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
