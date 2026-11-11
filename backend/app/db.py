# backend/app/db.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

engine_kwargs = {
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
}

if "sqlite" in DATABASE_URL:
    engine_kwargs = {"connect_args": {"check_same_thread": False}}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> bool:
    """Creates database schema if tables do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
        return True
    except Exception as exc:
        logger.error(
            f"Database initialization failed ({DATABASE_URL}): {exc}. "
            "Ensure PostgreSQL is running and credentials in DATABASE_URL are valid."
        )
        return False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
