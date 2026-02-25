from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db


def _make_client():
    from app import main as main_module

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    main_module.engine = engine

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[get_db] = override_get_db
    client = TestClient(main_module.app)
    return client, main_module.app


def _seller_headers(user_id: int, name: str, phone: str, subcity: str = "Bole") -> dict[str, str]:
    return {
        "x-user-id": str(user_id),
        "x-user-role": "seller",
        "x-user-name": name,
        "x-user-phone": phone,
        "x-user-subcity": subcity,
    }


def test_create_listing_requires_addis_subcity():
    client, app = _make_client()
    try:
        resp = client.post(
            "/listings",
            headers=_seller_headers(101, "Seller A", "+251911000101"),
            json={
                "title": "Office Chair",
                "category": "Office",
                "subcity": "Adama",
                "price_birr": 7000,
                "description": "Ergonomic chair",
            },
        )
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_patch_listing_forbidden_for_non_owner():
    client, app = _make_client()
    try:
        create_resp = client.post(
            "/listings",
            headers=_seller_headers(102, "Seller One", "+251911000102"),
            json={
                "title": "Coffee Table",
                "category": "Tables",
                "subcity": "Bole",
                "price_birr": 5000,
                "description": "Small table",
            },
        )
        listing_id = create_resp.json()["id"]

        patch_resp = client.patch(
            f"/listings/{listing_id}",
            headers=_seller_headers(103, "Seller Two", "+251911000103"),
            json={
                "title": "Coffee Table Updated",
                "category": "Tables",
                "subcity": "Yeka",
                "price_birr": 5500,
                "description": "Updated description",
            },
        )
        assert patch_resp.status_code == 403
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_public_listing_endpoints_never_expose_phone_and_filters_work():
    client, app = _make_client()
    try:
        headers = _seller_headers(104, "Seller Pub", "+251911000104")
        pay_resp = client.post(
            "/payments/seller-capacity",
            headers=headers,
            json={"slots": 2, "idempotency_key": "seller-cap-104"},
        )
        assert pay_resp.status_code == 200

        first = client.post(
            "/listings",
            headers=headers,
            json={
                "title": "Sofa Deluxe",
                "category": "Living",
                "subcity": "Bole",
                "price_birr": 15000,
                "description": "Comfortable sofa",
            },
        )
        second = client.post(
            "/listings",
            headers=headers,
            json={
                "title": "Bed Basic",
                "category": "Beds",
                "subcity": "Yeka",
                "price_birr": 8000,
                "description": "Simple bed",
            },
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["status"] == "draft"

        publish_one = client.post(f"/listings/{first.json()['id']}/publish", headers=headers)
        publish_two = client.post(f"/listings/{second.json()['id']}/publish", headers=headers)
        assert publish_one.status_code == 200
        assert publish_two.status_code == 200
        assert publish_one.json()["status"] == "published"

        filtered = client.get("/listings", params={"category": "Living", "min_price": 10000, "keyword": "Deluxe"})
        assert filtered.status_code == 200
        rows = filtered.json()
        assert len(rows) == 1
        assert rows[0]["title"] == "Sofa Deluxe"
        assert "phone" not in rows[0]
        assert "seller_phone" not in rows[0]

        detail = client.get(f"/listings/{first.json()['id']}")
        assert detail.status_code == 200
        payload = detail.json()
        assert payload["title"] == "Sofa Deluxe"
        assert "phone" not in payload
        assert "seller_phone" not in payload
    finally:
        app.dependency_overrides.clear()
        client.close()
