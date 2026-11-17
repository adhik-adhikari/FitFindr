"""Create the garments persistence foundation.

Revision ID: 20261117_01
Revises:
Create Date: 2026-11-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261117_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "garments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status", sa.Text(), server_default=sa.text("'draft'"), nullable=False
        ),
        sa.Column("image_key", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("garment_type", sa.Text(), nullable=True),
        sa.Column("primary_color", sa.Text(), nullable=True),
        sa.Column(
            "secondary_colors",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("pattern", sa.Text(), nullable=True),
        sa.Column("formality", sa.Text(), nullable=True),
        sa.Column(
            "style_tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("warmth", sa.Text(), nullable=True),
        sa.Column("material", sa.Text(), nullable=True),
        sa.Column("sleeve_length", sa.Text(), nullable=True),
        sa.Column("neckline", sa.Text(), nullable=True),
        sa.Column("fit", sa.Text(), nullable=True),
        sa.Column(
            "custom_tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "is_favorite", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "analysis_proposal",
            postgresql.JSONB(none_as_null=True),
            nullable=True,
        ),
        sa.Column("analysis_provider", sa.Text(), nullable=True),
        sa.Column("analysis_model", sa.Text(), nullable=True),
        sa.Column("analysis_schema_version", sa.Integer(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active')",
            name="status_valid",
        ),
        sa.CheckConstraint(
            "category IS NULL OR category IN ('top', 'bottom', 'shoes', 'outerwear')",
            name="category_valid",
        ),
        sa.CheckConstraint(
            "status <> 'active' OR ("
            "image_key IS NOT NULL AND image_key !~ '^[[:space:]]*$' AND "
            "category IS NOT NULL AND "
            "garment_type IS NOT NULL AND garment_type !~ '^[[:space:]]*$' AND "
            "primary_color IS NOT NULL AND primary_color !~ '^[[:space:]]*$'"
            ")",
            name="active_required_fields",
        ),
        sa.CheckConstraint(
            "image_key IS NULL OR image_key !~ '^[[:space:]]*$'",
            name="image_key_nonblank",
        ),
        sa.CheckConstraint(
            "garment_type IS NULL OR garment_type !~ '^[[:space:]]*$'",
            name="garment_type_nonblank",
        ),
        sa.CheckConstraint(
            "primary_color IS NULL OR primary_color !~ '^[[:space:]]*$'",
            name="primary_color_nonblank",
        ),
        sa.CheckConstraint(
            "("
            "analysis_proposal IS NULL AND analysis_provider IS NULL AND "
            "analysis_model IS NULL AND analysis_schema_version IS NULL AND "
            "analyzed_at IS NULL"
            ") OR ("
            "analysis_proposal IS NOT NULL AND "
            "jsonb_typeof(analysis_proposal) = 'object' AND "
            "analysis_provider IS NOT NULL AND "
            "analysis_provider !~ '^[[:space:]]*$' AND "
            "analysis_model IS NOT NULL AND "
            "analysis_model !~ '^[[:space:]]*$' AND "
            "analysis_schema_version IS NOT NULL AND analysis_schema_version > 0 AND "
            "analyzed_at IS NOT NULL"
            ")",
            name="analysis_complete",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth.users.id"],
            name="fk_garments_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_garments"),
        schema="public",
    )
    op.create_index(
        "ix_garments_user_status_category",
        "garments",
        ["user_id", "status", "category"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_garments_active_available_user_category",
        "garments",
        ["user_id", "category"],
        unique=False,
        schema="public",
        postgresql_where=sa.text("status = 'active' AND is_available = true"),
    )
    op.execute("ALTER TABLE public.garments ENABLE ROW LEVEL SECURITY")
    op.execute(
        "REVOKE ALL PRIVILEGES ON TABLE public.garments FROM anon, authenticated"
    )


def downgrade() -> None:
    op.drop_table("garments", schema="public")
