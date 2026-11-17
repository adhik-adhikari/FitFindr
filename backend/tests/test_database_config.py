import pytest
from pydantic import SecretStr, ValidationError

from app.config import DatabaseSettings


def test_database_settings_normalize_postgresql_for_async_psycopg() -> None:
    settings = DatabaseSettings(
        _env_file=None,
        database_url=SecretStr("postgresql://user:secret@localhost/fitfindr_test"),
    )

    assert settings.sqlalchemy_url.drivername == "postgresql+psycopg"
    assert settings.database_pool_size == 5
    assert settings.database_connect_timeout_seconds == 10
    assert "secret" not in repr(settings)


def test_database_pool_settings_are_bounded() -> None:
    with pytest.raises(ValidationError):
        DatabaseSettings(
            _env_file=None,
            database_url=SecretStr("postgresql://localhost/fitfindr_test"),
            database_pool_size=0,
        )


def test_database_settings_reject_a_non_postgresql_url() -> None:
    settings = DatabaseSettings(
        _env_file=None,
        database_url=SecretStr("sqlite:///fitfindr.db"),
    )

    with pytest.raises(ValueError, match="PostgreSQL"):
        _ = settings.sqlalchemy_url
