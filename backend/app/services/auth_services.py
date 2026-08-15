from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegister
from app.auth.hashing import hash_password
from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token


def register_user(user: UserRegister, db: Session):
    existing_email = db.query(User).filter(User.email == user.email).first()

    if existing_email:
        return None

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    access_token = create_access_token(
        {
            "sub": user.email,
            "user_id": user.id
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }