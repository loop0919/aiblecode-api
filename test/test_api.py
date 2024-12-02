import os
import uuid

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.crud import problem as problem_crud
from api.database import Base, get_db
from api.main import app
from api.models import problem as problem_model
from api.models.user import User
from api.schemas import problem as problem_schema
from api.utils import hash

# テスト用SQLiteデータベースを作成
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

load_dotenv(verbose=True)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# テスト用のデータベース依存関係を定義
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db

    finally:
        db.close()


# アプリケーションにモックを適用
app.dependency_overrides[get_db] = override_get_db


# データベースのセットアップとクライアントの準備
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # テスト用のテーブルを作成
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    admin_user = User(
        id=uuid.uuid4(),
        username="admin",
        password=hash.hash_password(ADMIN_PASSWORD),
        is_active=True,
    )
    session.add(admin_user)
    session.commit()
    session.close()

    yield
    # テスト後にテーブルを削除
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello World! Get started with the API at /api/docs."
    }


@pytest.fixture(scope="function")
def db_session():
    # 新しいテスト用DBセッションを提供
    session = TestingSessionLocal()
    yield session
    session.close()


def test_user(db_session: Session):
    # 未ログイン状態でのアクセス（401エラーが返ることを確認）
    response = client.get("/user_list")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # ユーザーを作成
    response = client.post("/signup", json={"username": "test", "password": "test"})
    assert response.status_code == 200
    assert response.json().get("status") == "success"

    # ログイン失敗
    response = client.post("/token", data={"username": "test", "password": "invalid"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

    # ログイン成功（アクセストークンがCookieに保存されることを確認）
    response = client.post("/token", data={"username": "test", "password": "test"})
    assert response.status_code == 200
    assert response.cookies.get("session") is not None

    # ログイン状態でのアクセス（ユーザーが1人のみであることを確認）
    response = client.get("/user_list")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert {res.get("username") for res in response.json()} == {"test", "admin"}

    # 重複してユーザーを作成できないことを確認
    response = client.post("/signup", json={"username": "test", "password": "test2"})
    assert response.status_code == 400
    assert response.json() == {"detail": "User already exists"}

    # ログアウト
    response = client.post("/logout")
    assert response.status_code == 200
    assert response.cookies.get("session") is None

    # ログアウト状態でのアクセス（401エラーが返ることを確認）
    response = client.get("/user_list")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_create_category(db_session: Session):
    # 未ログイン状態でのアクセス（401エラーが返ることを確認）
    response = client.post(
        "/create_category",
        json={
            "path_id": "test_category_failer",
            "title": "テスト入門(失敗)",
            "description": "これはテスト用のカテゴリです(失敗予定)",
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # adminでログイン成功（アクセストークンがCookieに保存されることを確認）
    response = client.post(
        "/token", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200
    assert response.cookies.get("session") is not None

    # ログイン状態でのアクセス（カテゴリを作成）
    response = client.post(
        "/create_category",
        json={
            "path_id": "test_category",
            "title": "テスト入門",
            "description": "これはテスト用のカテゴリです(成功予定)",
        },
    )
    assert response.status_code == 200

    # カテゴリが重複して作成されないことを確認
    response = client.post(
        "/create_category",
        json={
            "path_id": "test_category",
            "title": "テスト入門(アップデート)",
            "description": "これはテスト用のカテゴリです(アップデート)",
        },
    )
    assert response.status_code == 200
    assert db_session.query(problem_model.Category).count() == 1
    assert (
        db_session.query(problem_model.Category).first().title
        == "テスト入門(アップデート)"
    )

    response = client.get("/category_list")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0].get("title") == "テスト入門(アップデート)"

    # ログアウト
    response = client.post("/logout")
    assert response.status_code == 200


def test_create_category_not_admin(db_session: Session):
    # ログイン成功（アクセストークンがCookieに保存されることを確認）
    response = client.post("/token", data={"username": "test", "password": "test"})
    assert response.status_code == 200
    assert response.cookies.get("session") is not None

    # ログイン状態でのアクセス（権限がないため失敗することを確認）
    response = client.post(
        "/create_category",
        json={
            "path_id": "test_category",
            "title": "テスト入門",
            "description": "これはテスト用のカテゴリです(失敗予定)",
        },
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}

    # ログアウト
    response = client.post("/logout")
    assert response.status_code == 200


def test_create_problem(db_session: Session):
    # カテゴリを作成
    problem_crud.create_category(
        db_session,
        problem_schema.CategoryCreate(
            path_id="test_category",
            title="テスト入門",
            description="これはテスト用のカテゴリです(成功予定)",
        ),
    )

    # 未ログイン状態でのアクセス（401エラーが返ることを確認）
    response = client.post(
        "/create_problem",
        json={
            "path_id": "test_problem",
            "title": "テスト問題",
            "statement": "これはテスト用の問題です(失敗予定)",
            "category_path_id": "test_category",
            "time_limit": 1,
            "memory_limit": 128,
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # adminでログイン
    response = client.post(
        "/token", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200

    # ログイン状態でのアクセス（問題を作成）
    response = client.post(
        "/create_problem",
        json={
            "path_id": "test_problem",
            "title": "テスト問題",
            "statement": "これはテスト用の問題です(成功予定)",
            "category_path_id": "test_category",
            "time_limit": 1,
            "memory_limit": 128,
        },
    )
    assert response.status_code == 200

    # 問題が重複して作成されないことを確認
    response = client.post(
        "/create_problem",
        json={
            "path_id": "test_problem",
            "title": "テスト問題(アップデート)",
            "statement": "これはテスト用の問題です(アップデート予定)",
            "category_path_id": "test_category",
            "time_limit": 1,
            "memory_limit": 128,
        },
    )
    assert response.status_code == 200

    assert db_session.query(problem_model.Problem).count() == 1
    assert (
        db_session.query(problem_model.Problem).first().title
        == "テスト問題(アップデート)"
    )

    # 問題の一覧を取得
    response = client.get("/problem_list/test_category")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0].get("title") == "テスト問題(アップデート)"

    # ログアウト
    response = client.post("/logout")
    assert response.status_code == 200


def test_create_problem_not_admin(db_session: Session):
    # カテゴリを作成
    problem_crud.create_category(
        db_session,
        problem_schema.CategoryCreate(
            path_id="test_category",
            title="テスト入門",
            description="これはテスト用のカテゴリです(成功予定)",
        ),
    )

    # ログイン
    response = client.post("/token", data={"username": "test", "password": "test"})
    assert response.status_code == 200

    # ログイン状態でのアクセス（権限がないため失敗することを確認）
    response = client.post(
        "/create_problem",
        json={
            "path_id": "test_problem",
            "title": "テスト問題",
            "statement": "これはテスト用の問題です(失敗予定)",
            "category_path_id": "test_category",
            "time_limit": 1,
            "memory_limit": 128,
        },
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}

    # ログアウト
    response = client.post("/logout")
    assert response.status_code == 200
