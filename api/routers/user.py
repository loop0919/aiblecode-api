from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

from api import database
from api.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from api.core.security import (
    authenticate_user,
    create_access_token,
    create_session,
    delete_session,
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
)
from api.crud import user as user_crud
from api.models import user as user_model
from api.schemas import user as user_schema

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ユーザー一覧を返す
@router.get(
    "/user_list",
    tags=["user"],
    response_model=list[user_schema.User],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"}},
)
def user_list(
    user=Depends(get_current_active_user), db=Depends(database.get_db)
) -> list[user_schema.User]:
    """
    現在登録しているユーザーの一覧を取得する。
    ❗**一般ユーザーログインが必須**
    """
    return user_crud.get_user_list(db)


# ユーザー情報を返す
@router.get(
    "/user/{username}",
    tags=["user"],
    response_model=user_schema.UserFoundMessage,
)
def user_detail(
    username: str, db=Depends(database.get_db), user=Depends(get_current_active_user)
) -> user_schema.UserFoundMessage:
    """
    ユーザーの詳細情報を取得する。
    ❗**一般ユーザーログインが必須**
    """
    got_user = user_crud.get_user_by_username(db, username)

    return user_schema.UserFoundMessage(
        status="success",
        message="User found",
        user=user_schema.User(id=got_user.id, username=got_user.username),
    )


# ユーザー情報を返す
@router.get(
    "/my_user",
    tags=["user"],
    response_model=user_schema.UserFoundMessage,
)
def my_user_detail(
    user: user_model.User = Depends(get_current_active_user),
) -> user_schema.UserFoundMessage:
    """
    自分のユーザーの詳細情報を取得する。
    ❗**一般ユーザーログインが必須**
    """
    return user_schema.UserFoundMessage(
        status="success",
        message="User found",
        user=user_schema.User(id=user.id, username=user.username),
    )


# ユーザーが認証済みかどうかを返す
@router.get(
    "/is_authenticated",
    tags=["user"],
    response_model=user_schema.IsAuthenticated,
)
def is_authenticated(
    request: Request, db=Depends(database.get_db)
) -> user_schema.IsAuthenticated:
    """
    ユーザーが認証済みかどうかを返す。
    """
    try:
        # トークンを取得
        token = oauth2_scheme(request, db)

        # トークンからユーザーを取得
        current_user = get_current_user(token)

        # アクティブなユーザーか確認
        user = get_current_active_user(current_user, db)
        if not user:
            return user_schema.IsAuthenticated(is_authenticated=False)
    except ValueError:
        # トークンの検証エラー
        return user_schema.IsAuthenticated(is_authenticated=False)
    except Exception:
        # その他のエラー
        return user_schema.IsAuthenticated(is_authenticated=False)

    # 認証成功
    return user_schema.IsAuthenticated(is_authenticated=True)


# 新規のユーザー情報(username, password)を受信後、ユーザーを作成
@router.post(
    "/signup",
    tags=["user"],
    response_model=user_schema.UserCreateResponse,
    responses={status.HTTP_400_BAD_REQUEST: {"description": "User already exists"}},
)
def signup(
    model: user_schema.UserCreate, db=Depends(database.get_db)
) -> user_schema.UserCreateResponse:
    """
    新規のユーザーを登録する。
    """
    created = user_crud.create_user(db, user=model)

    return user_schema.UserCreateResponse(
        status="success",
        message="User created successfully",
        user=user_schema.User(id=created.id, username=created.username),
    )


# ログイン情報を受信後、セッションIDを生成してHttpOnly Cookieに保存
@router.post(
    "/token",
    tags=["user"],
    response_model=user_schema.Message,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Incorrect username or password"}
    },
)
def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db=Depends(database.get_db),
) -> user_schema.Message:
    """
    ユーザー名とパスワードを受け取り、セッションIDを生成する。
    """
    user = authenticate_user(db, form_data.username, form_data.password)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    session_id = create_session(db, access_token)

    response.set_cookie(
        key="session",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="none",
        expires=access_token_expires.total_seconds(),
    )

    return user_schema.Message(status="success", message="Login successful")


@router.post("/logout", tags=["user"], response_model=user_schema.Message)
def logout(
    request: Request, response: Response, db=Depends(database.get_db)
) -> user_schema.Message:
    """
    ログアウトする。
    """
    session_id = request.cookies.get("session")
    if session_id:
        delete_session(db, session_id)

    response.delete_cookie("session")
    return user_schema.Message(status="success", message="Logout successful")
