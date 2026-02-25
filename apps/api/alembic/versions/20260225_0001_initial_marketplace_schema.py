"""initial marketplace schema

Revision ID: 20260225_0001
Revises:
Create Date: 2026-02-25 21:40:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260225_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )

    op.create_table(
        "subcities",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_addis", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", name="uq_subcities_name"),
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("seller_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("subcity_id", sa.BigInteger(), sa.ForeignKey("subcities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("price_birr", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_listings_category_id", "listings", ["category_id"])
    op.create_index("ix_listings_subcity_id", "listings", ["subcity_id"])
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_index("ix_listings_price_birr", "listings", ["price_birr"])
    op.create_index(
        "ix_listings_search",
        "listings",
        ["category_id", "subcity_id", "status", "price_birr"],
    )

    op.create_table(
        "listing_images",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("listing_id", sa.BigInteger(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_listing_images_listing_id", "listing_images", ["listing_id"])

    op.create_table(
        "plan_catalog",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("min_slots", sa.Integer(), nullable=False),
        sa.Column("max_slots", sa.Integer(), nullable=True),
        sa.Column("price_birr", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_plan_catalog_code"),
    )

    op.create_table(
        "seller_plans",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("seller_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_catalog_id", sa.BigInteger(), sa.ForeignKey("plan_catalog.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("slots_total", sa.Integer(), nullable=False),
        sa.Column("slots_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_seller_plans_seller_id", "seller_plans", ["seller_id"])

    op.create_table(
        "credit_packages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_count", sa.Integer(), nullable=False),
        sa.Column("price_birr", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_credit_packages_code"),
    )

    op.create_table(
        "buyer_credit_wallet",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("buyer_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credits_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("buyer_id", "category_id", name="uq_wallet_buyer_category"),
    )

    op.create_table(
        "credit_unlocks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("buyer_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seller_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", sa.BigInteger(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=True),
        sa.Column("credits_spent", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("buyer_id", "seller_id", "category_id", name="uq_credit_unlock_buyer_seller_category"),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("listing_id", sa.BigInteger(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("buyer_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seller_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("listing_id", "buyer_id", "seller_id", name="uq_conversation_triplet"),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_ref", sa.String(length=120), nullable=False),
        sa.Column("amount_birr", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="ETB"),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "provider_ref", name="uq_payments_provider_ref"),
    )

    op.create_table(
        "purchases",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("payment_id", sa.BigInteger(), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("amount_birr", sa.Integer(), nullable=False),
        sa.Column("applied", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_purchases_payment_id", "purchases", ["payment_id"], unique=True)

    op.create_table(
        "reports",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("reporter_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("listing_id", sa.BigInteger(), sa.ForeignKey("listings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reported_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "admin_actions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("admin_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(length=60), nullable=False),
        sa.Column("target_table", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("admin_actions")
    op.drop_table("reports")
    op.drop_index("ix_purchases_payment_id", table_name="purchases")
    op.drop_table("purchases")
    op.drop_table("payments")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("credit_unlocks")
    op.drop_table("buyer_credit_wallet")
    op.drop_table("credit_packages")
    op.drop_index("ix_seller_plans_seller_id", table_name="seller_plans")
    op.drop_table("seller_plans")
    op.drop_table("plan_catalog")
    op.drop_index("ix_listing_images_listing_id", table_name="listing_images")
    op.drop_table("listing_images")
    op.drop_index("ix_listings_search", table_name="listings")
    op.drop_index("ix_listings_price_birr", table_name="listings")
    op.drop_index("ix_listings_status", table_name="listings")
    op.drop_index("ix_listings_subcity_id", table_name="listings")
    op.drop_index("ix_listings_category_id", table_name="listings")
    op.drop_table("listings")
    op.drop_table("subcities")
    op.drop_table("categories")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_table("users")
