import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import get_password_hash, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Retrieves a user by UUID."""
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieves a user by email address."""
    return db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Creates a new user record in the database."""
    user = User(
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Canonical user authentication helper.
    Verifies user exists and password is valid.
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
