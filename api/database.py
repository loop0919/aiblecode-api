from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from api.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    with SessionLocal() as session:
        yield session
