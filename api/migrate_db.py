import os
import pathlib
import uuid

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.models.problem import Base as problem_base
from api.models.submission import Base as submission_base
from api.models.user import Base as user_base
from api.models.user import User
from api.utils import hash

load_dotenv(verbose=True)
dotenv_path = pathlib.Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path)

DATABASE_URL = "sqlite:///./judge.db"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

engine = create_engine(DATABASE_URL)

bases = [user_base, problem_base, submission_base]


def reset_database():
    """
    データベースを初期化する。
    """
    for base in bases:
        base.metadata.drop_all(engine)
        base.metadata.create_all(engine)

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


if __name__ == "__main__":
    reset_database()
    print("Database initialized")
