from __future__ import annotations

import os
from sqlalchemy import create_engine, text

DEFAULT_DB_URL = "postgresql+psycopg://chedtera:chedtera@localhost:5432/chedtera"

ADDIS_SUBCITIES = [
    "Addis Ketema",
    "Akaky Kaliti",
    "Arada",
    "Bole",
    "Gullele",
    "Kirkos",
    "Kolfe Keranio",
    "Lemi Kura",
    "Lideta",
    "Nifas Silk-Lafto",
    "Yeka",
]

CATEGORIES = [
    ("beds", "Beds"),
    ("sofas", "Sofas"),
    ("tables", "Tables"),
    ("wardrobes", "Wardrobes"),
    ("electronics", "Electronics"),
]

PLAN_TIERS = [
    ("seller_1_5", "Seller 1-5 listings", 1, 5, 200),
    ("seller_6_10", "Seller 6-10 listings", 6, 10, 250),
    ("seller_gt_10", "Seller >10 listings", 11, None, 500),
]


def seed_subcities(conn) -> None:
    for name in ADDIS_SUBCITIES:
        conn.execute(
            text(
                """
                INSERT INTO subcities (name, is_addis)
                VALUES (:name, true)
                ON CONFLICT (name) DO NOTHING
                """
            ),
            {"name": name},
        )


def seed_categories(conn) -> None:
    for slug, name in CATEGORIES:
        conn.execute(
            text(
                """
                INSERT INTO categories (slug, name, is_active)
                VALUES (:slug, :name, true)
                ON CONFLICT (slug) DO NOTHING
                """
            ),
            {"slug": slug, "name": name},
        )


def seed_plan_tiers(conn) -> None:
    for code, name, min_slots, max_slots, price in PLAN_TIERS:
        conn.execute(
            text(
                """
                INSERT INTO plan_catalog (code, name, min_slots, max_slots, price_birr, is_active)
                VALUES (:code, :name, :min_slots, :max_slots, :price_birr, true)
                ON CONFLICT (code) DO UPDATE
                SET name = EXCLUDED.name,
                    min_slots = EXCLUDED.min_slots,
                    max_slots = EXCLUDED.max_slots,
                    price_birr = EXCLUDED.price_birr,
                    is_active = true
                """
            ),
            {
                "code": code,
                "name": name,
                "min_slots": min_slots,
                "max_slots": max_slots,
                "price_birr": price,
            },
        )


def seed_credit_packages(conn) -> None:
    rows = conn.execute(text("SELECT id, slug, name FROM categories")).mappings().all()
    for row in rows:
        code = f"{row['slug']}_10_contacts"
        pkg_name = f"{row['name']} - 10 contacts"
        conn.execute(
            text(
                """
                INSERT INTO credit_packages (code, name, category_id, contact_count, price_birr, is_active)
                VALUES (:code, :name, :category_id, 10, 100, true)
                ON CONFLICT (code) DO UPDATE
                SET name = EXCLUDED.name,
                    category_id = EXCLUDED.category_id,
                    contact_count = EXCLUDED.contact_count,
                    price_birr = EXCLUDED.price_birr,
                    is_active = true
                """
            ),
            {
                "code": code,
                "name": pkg_name,
                "category_id": row["id"],
            },
        )


def run_seed() -> None:
    database_url = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    engine = create_engine(database_url, future=True)

    with engine.begin() as conn:
        seed_subcities(conn)
        seed_categories(conn)
        seed_plan_tiers(conn)
        seed_credit_packages(conn)

    print("Seed complete: subcities, categories, plan tiers, and credit packages.")


if __name__ == "__main__":
    run_seed()
