import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Phase 1: SQLite. Later, just set DATABASE_URL env var to a Postgres URL
# e.g. postgresql://user:password@localhost:5432/erp_db
# and nothing else in the codebase needs to change.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./erp.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
