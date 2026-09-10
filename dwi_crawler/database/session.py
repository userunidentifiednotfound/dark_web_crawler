"""Database connection, engine configuration, and session management."""

from collections.abc import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from dwi_crawler.config.settings import get_settings


class Base(DeclarativeBase):
    """Base model for all DWI crawler database entities."""
    pass


_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None
_sync_engine = None
_sync_session_factory: sessionmaker[Session] | None = None


def get_async_engine() -> AsyncEngine:
    global _async_engine
    if _async_engine is None:
        settings = get_settings()
        connect_args = {}
        if "sqlite" in settings.dwi_database_url:
            connect_args = {"check_same_thread": False}
        _async_engine = create_async_engine(
            settings.dwi_database_url,
            echo=False,
            future=True,
            connect_args=connect_args,
        )
    return _async_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_async_engine()
        _async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields an async session context."""
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        connect_args = {}
        if "sqlite" in settings.sync_database_url:
            connect_args = {"check_same_thread": False}
        _sync_engine = create_engine(
            settings.sync_database_url,
            echo=False,
            connect_args=connect_args,
        )
    return _sync_engine


def get_sync_session() -> Session:
    global _sync_session_factory
    if _sync_session_factory is None:
        engine = get_sync_engine()
        _sync_session_factory = sessionmaker(bind=engine, autoflush=False)
    return _sync_session_factory()


async def init_db() -> None:
    """Initializes all database tables asynchronously."""
    # Ensure all models are loaded before table creation
    import dwi_crawler.models  # noqa: F401
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_health() -> bool:
    """Performs a simple connectivity check against the configured database."""
    try:
        from sqlalchemy import text
        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
