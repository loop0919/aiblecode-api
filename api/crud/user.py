import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.models import user as user_model
from api.schemas import user as user_schema
from api.utils.hash import hash_password


def get_user(db: Session, user_id: uuid.UUID) -> user_model.User:
    return db.query(user_model.User).filter(user_model.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> user_model.User:
    return (
        db.query(user_model.User).filter(user_model.User.username == username).first()
    )


def get_user_list(db: Session) -> list[user_model.User]:
    return db.query(user_model.User).all()


def create_user(db: Session, user: user_schema.UserCreate) -> user_model.User:
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )

    hashed_password = hash_password(user.password)

    db_user = user_model.User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_session(db: Session, id: str) -> user_model.Session:
    return db.query(user_model.Session).filter(user_model.Session.id == id).first()
