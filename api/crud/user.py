from sqlalchemy.orm import Session
from api.models import user as user_model
from api.schemas import user as user_schema
from api.utils.hash import hash_password

import uuid


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
        return None

    hashed_password = hash_password(user.password)

    db_user = user_model.User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
