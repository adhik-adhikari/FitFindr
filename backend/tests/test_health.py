from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient

from app.db.session import DatabaseRuntime
from app.main import create_app


def test_health_is_public_and_lightweight() -> None:
    settings_factory = Mock(side_effect=AssertionError("health loaded DB settings"))
    app = create_app()

    with TestClient(app) as client:
        app.state.database._settings_factory = settings_factory
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    settings_factory.assert_not_called()


def test_cors_allows_only_configured_origin(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    client = TestClient(create_app())

    allowed = client.get("/health", headers={"Origin": "http://localhost:3000"})
    other = client.get("/health", headers={"Origin": "http://other.local"})

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in other.headers


def test_lifespan_disposes_database_runtime(monkeypatch) -> None:
    runtime = DatabaseRuntime()
    dispose = AsyncMock()
    monkeypatch.setattr(runtime, "dispose", dispose)
    monkeypatch.setattr("app.main.DatabaseRuntime", Mock(return_value=runtime))

    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200

    dispose.assert_awaited_once_with()
