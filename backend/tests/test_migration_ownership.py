import ast
from pathlib import Path
from types import SimpleNamespace

from app.db.base import (
    Base,
    include_migration_name,
    include_migration_object,
)


def test_alembic_owns_only_public_garments() -> None:
    assert include_migration_name("public", "schema", {})
    assert include_migration_name("garments", "table", {"schema_name": "public"})

    for schema_name in ("auth", "storage", "realtime", "vault", "extensions"):
        assert not include_migration_name(schema_name, "schema", {})
        assert not include_migration_name(
            "provider_table", "table", {"schema_name": schema_name}
        )
    assert not include_migration_name(
        "provider_managed_sentinel", "table", {"schema_name": "public"}
    )


def test_external_auth_metadata_resolves_fk_without_becoming_owned() -> None:
    auth_users = Base.metadata.tables["auth.users"]

    assert auth_users.info["externally_managed"] is True
    assert not include_migration_object(
        auth_users,
        "users",
        "table",
        False,
        None,
    )
    assert not include_migration_object(
        SimpleNamespace(info={}, schema="storage"),
        "objects",
        "table",
        True,
        None,
    )


def test_application_code_never_calls_metadata_create_all() -> None:
    app_directory = Path(__file__).resolve().parents[1] / "app"
    forbidden_calls = []
    for path in app_directory.rglob("*.py"):
        tree = ast.parse(path.read_text())
        forbidden_calls.extend(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_all"
        )

    assert forbidden_calls == []
