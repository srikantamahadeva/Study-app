"""Database engine and session management.

In development, an empty DATABASE_URL starts an embedded PostgreSQL server
(pgserver, no root required). Production provides DATABASE_URL explicitly.
"""

from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def _embedded_server_uri() -> str:
    import pgserver

    data_dir = Path("data/embedded-pg").resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    server = pgserver.get_server(str(data_dir))
    # cleanup_mode="stop": keep data across restarts, stop when process exits.
    return server.get_uri()


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    url = settings.database_url or _embedded_server_uri()
    return create_engine(url, pool_pre_ping=True, future=True)


def new_session() -> Session:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)()


def session_scope() -> Generator[Session, None, None]:
    session = new_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping() -> bool:
    with get_engine().connect() as conn:
        return conn.execute(text("SELECT 1")).scalar() == 1


def reset_engine_cache() -> None:
    """Test hook: drop cached engine/server after tests change the URL."""
    get_engine.cache_clear()
    _embedded_server_uri.cache_clear()
