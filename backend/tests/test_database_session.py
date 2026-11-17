import asyncio
from unittest.mock import Mock

from pydantic import SecretStr

from app.config import DatabaseSettings
from app.db.session import DatabaseRuntime


def test_database_runtime_is_lazy_and_disposes_engine(monkeypatch) -> None:
    settings_factory = Mock(side_effect=AssertionError("settings loaded too early"))
    runtime = DatabaseRuntime(settings_factory=settings_factory)

    assert not runtime.initialized
    settings_factory.assert_not_called()

    settings = DatabaseSettings(
        _env_file=None,
        database_url=SecretStr("postgresql://localhost/fitfindr_test"),
    )

    async def exercise_lifecycle() -> None:
        await runtime.initialize(settings)
        assert runtime.initialized
        settings_factory.assert_not_called()

        engine = runtime._engine
        assert engine is not None
        sync_dispose = Mock()
        monkeypatch.setattr("sqlalchemy.engine.Engine.dispose", sync_dispose)

        await runtime.dispose()
        sync_dispose.assert_called_once()
        assert not runtime.initialized

    asyncio.run(exercise_lifecycle())
