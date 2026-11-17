from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Garment(Base):
    __tablename__ = "garments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active')",
            name="status_valid",
        ),
        CheckConstraint(
            "category IS NULL OR category IN ('top', 'bottom', 'shoes', 'outerwear')",
            name="category_valid",
        ),
        CheckConstraint(
            "status <> 'active' OR ("
            "image_key IS NOT NULL AND image_key !~ '^[[:space:]]*$' AND "
            "category IS NOT NULL AND "
            "garment_type IS NOT NULL AND garment_type !~ '^[[:space:]]*$' AND "
            "primary_color IS NOT NULL AND primary_color !~ '^[[:space:]]*$'"
            ")",
            name="active_required_fields",
        ),
        CheckConstraint(
            "image_key IS NULL OR image_key !~ '^[[:space:]]*$'",
            name="image_key_nonblank",
        ),
        CheckConstraint(
            "garment_type IS NULL OR garment_type !~ '^[[:space:]]*$'",
            name="garment_type_nonblank",
        ),
        CheckConstraint(
            "primary_color IS NULL OR primary_color !~ '^[[:space:]]*$'",
            name="primary_color_nonblank",
        ),
        CheckConstraint(
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
        Index(
            "ix_garments_user_status_category",
            "user_id",
            "status",
            "category",
        ),
        Index(
            "ix_garments_active_available_user_category",
            "user_id",
            "category",
            postgresql_where=text("status = 'active' AND is_available = true"),
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'draft'"),
    )
    image_key: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    garment_type: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str | None] = mapped_column(Text)
    secondary_colors: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("'{}'::text[]"),
    )
    pattern: Mapped[str | None] = mapped_column(Text)
    formality: Mapped[str | None] = mapped_column(Text)
    style_tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("'{}'::text[]"),
    )
    warmth: Mapped[str | None] = mapped_column(Text)
    material: Mapped[str | None] = mapped_column(Text)
    sleeve_length: Mapped[str | None] = mapped_column(Text)
    neckline: Mapped[str | None] = mapped_column(Text)
    fit: Mapped[str | None] = mapped_column(Text)
    custom_tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("'{}'::text[]"),
    )
    note: Mapped[str | None] = mapped_column(Text)
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    analysis_proposal: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True)
    )
    analysis_provider: Mapped[str | None] = mapped_column(Text)
    analysis_model: Mapped[str | None] = mapped_column(Text)
    analysis_schema_version: Mapped[int | None] = mapped_column(Integer)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
