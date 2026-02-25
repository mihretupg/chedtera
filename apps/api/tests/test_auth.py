import logging
import re

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.models import User


def _extract_otp_from_logs(caplog) -> str:
    for record in reversed(caplog.records):
        match = re.search(r"otp=(\d{6})", record.getMessage())
        if match:
            return match.group(1)
    raise AssertionError("OTP not found in logs")


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
    return client, SessionLocal, main_module.app


def test_otp_flow_returns_jwt_and_me(monkeypatch, caplog):
    monkeypatch.setenv("APP_ENV", "dev")
    caplog.set_level(logging.INFO, logger="app.auth")
    client, _, app = _make_client()

    try:
        request_resp = client.post(
            "/auth/request-otp",
            json={
                "phone": "+251900111222",
                "full_name": "Buyer One",
                "role": "buyer",
                "subcity": "Bole",
            },
        )
        assert request_resp.status_code == 200
        otp = _extract_otp_from_logs(caplog)

        verify_resp = client.post("/auth/verify-otp", json={"phone": "+251900111222", "otp": otp})
        assert verify_resp.status_code == 200
        token = verify_resp.json()["access_token"]

        me_resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        payload = me_resp.json()
        assert payload["phone"] == "+251900111222"
        assert payload["role"] == "buyer"
        assert payload["subcity"] == "bole"
        assert payload["is_banned"] is False
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_otp_rate_limit(monkeypatch, caplog):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("OTP_RATE_LIMIT_MAX_REQUESTS", "1")
    caplog.set_level(logging.INFO, logger="app.auth")
    client, _, app = _make_client()

    try:
        first = client.post(
            "/auth/request-otp",
            json={
                "phone": "+251900333444",
                "full_name": "Buyer Two",
                "role": "buyer",
                "subcity": "Yeka",
            },
        )
        second = client.post(
            "/auth/request-otp",
            json={
                "phone": "+251900333444",
                "full_name": "Buyer Two",
                "role": "buyer",
                "subcity": "Yeka",
            },
        )
        assert first.status_code == 200
        assert second.status_code == 429
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_banned_user_cannot_verify(monkeypatch, caplog):
    monkeypatch.setenv("APP_ENV", "dev")
    caplog.set_level(logging.INFO, logger="app.auth")
    client, SessionLocal, app = _make_client()

    try:
        create_otp = client.post(
            "/auth/request-otp",
            json={
                "phone": "+251900555666",
                "full_name": "Seller One",
                "role": "seller",
                "subcity": "Arada",
            },
        )
        assert create_otp.status_code == 200
        otp = _extract_otp_from_logs(caplog)
        first_verify = client.post("/auth/verify-otp", json={"phone": "+251900555666", "otp": otp})
        assert first_verify.status_code == 200

        with SessionLocal.begin() as db:
            user = db.execute(select(User).where(User.phone == "+251900555666")).scalar_one()
            user.is_banned = True

        create_otp_again = client.post(
            "/auth/request-otp",
            json={
                "phone": "+251900555666",
                "full_name": "Seller One",
                "role": "seller",
                "subcity": "Arada",
            },
        )
        assert create_otp_again.status_code == 200
        otp_again = _extract_otp_from_logs(caplog)
        second_verify = client.post("/auth/verify-otp", json={"phone": "+251900555666", "otp": otp_again})
        assert second_verify.status_code == 403
        assert second_verify.json()["detail"] == "User is banned"
    finally:
        app.dependency_overrides.clear()
        client.close()
