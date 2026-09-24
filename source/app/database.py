"""Database engine, session factory and declarative base."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

DATABASE_URL = os.getenv("DATABASE_URL") or get_settings().database_url

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Yields a DB session per request and closes it in finally."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
