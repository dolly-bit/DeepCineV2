from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.user import UserRegister, UserResponse, UserLogin, Token
from app.services.auth_services import register_user, login_user
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=UserResponse)
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    new_user = register_user(user, db)

    if not new_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return new_user


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    result = login_user(
        credentials.email,
        credentials.password,
        db
    )

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"],
        "user_id": result["user"].id,
        "username": result["user"].username
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of whoever the bearer token belongs to. The
    Profile page uses this both to display real account info and, just
    as importantly, as a validity check: if the stored token is stale,
    expired, or points at a user that no longer exists, this 401s and
    the frontend's response interceptor clears the dead session
    automatically instead of leaving the UI stuck looking "logged in".
    """
    return current_user