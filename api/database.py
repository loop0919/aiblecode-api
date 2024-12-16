from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from api.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # プールの最大接続数
    max_overflow=10,  # プールを超えた場合の追加接続数
    pool_timeout=30,  # 接続待機時間
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    with SessionLocal() as session:
        yield session
