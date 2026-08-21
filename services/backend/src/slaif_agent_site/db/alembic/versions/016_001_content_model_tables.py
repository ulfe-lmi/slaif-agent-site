"""Create configurable content model tables as COW-enabled triplets.

Architecture reference: ARCHITECTURE-for-agents.md §10 (logical COW content
model). Tables are created via raw SQL inside ``op.execute()`` because the COW
foundation requires specific column ordering and constraint placement that
Alembic's declarative ``op.create_table()`` cannot express.

All DDL is additive; no existing tables are altered or dropped.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "016_001"
down_revision: str | Sequence[str] | None = "015_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE "content"."content_type" (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES control.site(id),
            key TEXT NOT NULL,
            labels JSONB NOT NULL DEFAULT '{}',
            slug_pattern TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            definition_version INTEGER NOT NULL DEFAULT 1,
            settings JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_content_type_site_key
            ON "content"."content_type" (site_id, key)
        """
    )

    op.execute(
        """
        CREATE TABLE "content"."field_definition" (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            type_id UUID NOT NULL REFERENCES content.content_type(id),
            key TEXT NOT NULL,
            label TEXT NOT NULL,
            field_type TEXT NOT NULL,
            required BOOLEAN NOT NULL DEFAULT false,
            localized BOOLEAN NOT NULL DEFAULT false,
            cardinality INTEGER NOT NULL DEFAULT 1,
            position INTEGER NOT NULL DEFAULT 0,
            validation JSONB NOT NULL DEFAULT '{}',
            ui_options JSONB NOT NULL DEFAULT '{}',
            definition_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_field_definition_type_key
            ON "content"."field_definition" (type_id, key)
        """
    )

    op.execute(
        """
        CREATE TABLE "content"."content_item" (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES control.site(id),
            type_id UUID NOT NULL REFERENCES content.content_type(id),
            slug TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            type_definition_version INTEGER NOT NULL,
            values JSONB NOT NULL DEFAULT '{}',
            row_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_content_item_site_type_slug
            ON "content"."content_item" (site_id, type_id, slug)
        """
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS "content"."content_item" CASCADE')
    op.execute('DROP TABLE IF EXISTS "content"."field_definition" CASCADE')
    op.execute('DROP TABLE IF EXISTS "content"."content_type" CASCADE')
