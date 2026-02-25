"""add listing statuses

Revision ID: 20260225_0003
Revises: 20260225_0002
Create Date: 2026-02-25 22:55:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260225_0003"
down_revision = "20260225_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    listing_status = sa.Enum("DRAFT", "PUBLISHED", "SOLD", "ARCHIVED", "HIDDEN", name="listingstatus")
    listing_status.create(op.get_bind(), checkfirst=True)
    op.add_column("listings", sa.Column("status", listing_status, nullable=True))
    op.execute("UPDATE listings SET status = 'PUBLISHED' WHERE is_published = true")
    op.execute("UPDATE listings SET status = 'DRAFT' WHERE status IS NULL")
    op.alter_column("listings", "status", nullable=False)
    op.create_index("ix_listings_status", "listings", ["status"])


def downgrade() -> None:
    op.drop_index("ix_listings_status", table_name="listings")
    op.drop_column("listings", "status")
    listing_status = sa.Enum("DRAFT", "PUBLISHED", "SOLD", "ARCHIVED", "HIDDEN", name="listingstatus")
    listing_status.drop(op.get_bind(), checkfirst=True)
