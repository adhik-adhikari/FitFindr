import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import DatabaseSettings


def create_database_engine(settings: DatabaseSettings) -> AsyncEngine:
    return create_async_engine(
        settings.sqlalchemy_url,
        connect_args={
            "connect_timeout": settings.database_connect_timeout_seconds,
        },
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        pool_pre_ping=True,
    )


class DatabaseRuntime:
    """Lazily owns one process-wide engine and its session factory."""

    def __init__(
        self,
        settings_factory: Callable[[], DatabaseSettings] = DatabaseSettings,
    ) -> None:
        self._settings_factory = settings_factory
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._initialize_lock = asyncio.Lock()

    @property
    def initialized(self) -> bool:
        return self._engine is not None

    async def initialize(self, settings: DatabaseSettings | None = None) -> None:
        if self._engine is not None:
            return
        async with self._initialize_lock:
            if self._engine is not None:
                return
            engine = create_database_engine(settings or self._settings_factory())
            self._engine = engine
            self._session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

    @asynccontextmanager
    async def session(
        self,
        settings: DatabaseSettings | None = None,
    ) -> AsyncIterator[AsyncSession]:
        await self.initialize(settings)
        session_factory = self._session_factory
        if session_factory is None:  # pragma: no cover - defensive invariant
            raise RuntimeError("database session factory was not initialized")
        async with session_factory() as session:
            # Services own commit/rollback decisions; this boundary only closes.
            yield session

    async def dispose(self) -> None:
        async with self._initialize_lock:
            engine = self._engine
            self._engine = None
            self._session_factory = None
        if engine is not None:
            await engine.dispose()


async def get_database_session(request: Request) -> AsyncIterator[AsyncSession]:
    runtime: DatabaseRuntime = request.app.state.database
    async with runtime.session() as session:
        yield session
