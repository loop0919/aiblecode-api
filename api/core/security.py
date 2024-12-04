from datetime import datetime, timedelta, timezone
from secrets import token_hex

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
import jwt

from api import database
from api.utils.hash import verify_password
import api.crud.user as user_crud
import api.models.user as user_model
from api.core.config import SECRET_KEY, ALGORITHM

SESSION_ID_LENGTH = 64


def authenticate_user(db: Session, username: str, password: str):
    user = user_crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def create_access_token(data: dict, expires_delta: timedelta = 15):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_token_from_session(db: Session, request: Request) -> str | None:
    session_id = request.cookies.get("session")
    if not session_id:
        return None

    session = user_crud.get_session(db, session_id)
    if not session:
        return None

    return session.token


def create_session(db: Session, token: str) -> str:
    while True:
        session_id = token_hex(SESSION_ID_LENGTH)
        if not user_crud.get_session(db, session_id):
            break

    session = user_model.Session(id=session_id, token=f"Bearer {token}")
    db.add(session)
    db.commit()
    return session_id


def delete_session(db: Session, session_id: str):
    session = user_crud.get_session(db, session_id)
    if session:
        db.delete(session)
        db.commit()


# HeaderまたはCookieからjwtトークンを認証
class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(
        self, request: Request, db: Session = Depends(database.get_db)
    ) -> str | None:
        authorization: str = get_token_from_session(db, request)

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None

        return param


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    return username


def get_current_active_user(
    current_username: str = Depends(get_current_user),
    db: Session = Depends(database.get_db),
) -> user_model.User:
    user = user_crud.get_user_by_username(db, current_username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
