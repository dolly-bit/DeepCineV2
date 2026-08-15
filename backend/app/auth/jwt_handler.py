from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.config import settings


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str):
    """Returns the decoded payload, or None if the token is missing,
    malformed, expired, or signed with a different SECRET_KEY (e.g. a
    token issued before the server's secret was rotated)."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None