from sqlalchemy import Column, MetaData, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

OWNED_SCHEMAS = frozenset({None, "public"})
# Every future FitFindr-owned table must be intentionally added here; absence
# protects provider-managed and unrelated public tables from autogenerate.
OWNED_TABLES = frozenset({(None, "garments"), ("public", "garments")})

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    # Alembic is the only schema creation/evolution mechanism. Application
    # code must never call Base.metadata.create_all().
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Supabase owns this table. Declaring only its key lets SQLAlchemy resolve the
# cross-schema foreign key without introducing an application User model.
auth_users = Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    schema="auth",
    info={"externally_managed": True},
)


def include_migration_name(name, type_, parent_names) -> bool:
    """Allow Alembic reflection only for FitFindr-owned application objects."""
    if type_ == "schema":
        return name in OWNED_SCHEMAS
    if type_ == "table":
        return (parent_names.get("schema_name"), name) in OWNED_TABLES
    return True


def include_migration_object(object_, name, type_, reflected, compare_to) -> bool:
    """Exclude managed-provider metadata and all non-FitFindr tables."""
    if type_ != "table":
        return True
    if object_.info.get("externally_managed", False):
        return False
    return (object_.schema, name) in OWNED_TABLES
