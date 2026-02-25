"""add auth otp and user profile fields

Revision ID: 20260225_0002
Revises: 20260225_0001
Create Date: 2026-02-25 22:25:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260225_0002"
down_revision = "20260225_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("subcity", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("is_banned", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.execute("UPDATE users SET subcity = 'bole' WHERE subcity IS NULL")
    op.alter_column("users", "subcity", nullable=False)
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    op.create_table(
        "otp_request_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_otp_request_logs_phone", "otp_request_logs", ["phone"])

    op.create_table(
        "otp_challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.Enum("BUYER", "SELLER", name="userrole"), nullable=False),
        sa.Column("subcity", sa.String(length=64), nullable=False),
        sa.Column("otp_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_otp_challenges_phone", "otp_challenges", ["phone"])


def downgrade() -> None:
    op.drop_index("ix_otp_challenges_phone", table_name="otp_challenges")
    op.drop_table("otp_challenges")

    op.drop_index("ix_otp_request_logs_phone", table_name="otp_request_logs")
    op.drop_table("otp_request_logs")

    op.drop_index("ix_users_phone", table_name="users")
    op.drop_column("users", "is_banned")
    op.drop_column("users", "subcity")
