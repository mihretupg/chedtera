import hashlib
import hmac
import json
import logging
import os
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .locations import enforce_addis_subcity
from .models import OtpChallenge, OtpRequestLog, User, UserRole

logger = logging.getLogger("app.auth")


@lru_cache(maxsize=1)
def _get_redis_client():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    try:
        import redis
    except ImportError:
        logger.warning("REDIS_URL is configured but redis package is not installed; falling back to DB OTP store")
        return None
    return redis.Redis.from_url(redis_url, decode_responses=True)


def _otp_ttl_seconds() -> int:
    return int(os.getenv("OTP_TTL_SECONDS", "300"))


def _otp_rate_limit_window_seconds() -> int:
    return int(os.getenv("OTP_RATE_LIMIT_WINDOW_SECONDS", "3600"))


def _otp_rate_limit_max_requests() -> int:
    return int(os.getenv("OTP_RATE_LIMIT_MAX_REQUESTS", "5"))


def _jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-jwt-secret")


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _jwt_exp_minutes() -> int:
    return int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "1440"))


def _is_dev_mode() -> bool:
    return os.getenv("APP_ENV", "dev").lower() in {"dev", "development", "local"}


def normalize_phone(phone: str) -> str:
    return phone.strip()


def hash_otp(otp: str) -> str:
    otp_secret = os.getenv("OTP_HASH_SECRET", _jwt_secret())
    return hashlib.sha256(f"{otp}:{otp_secret}".encode("utf-8")).hexdigest()


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def request_otp(
    db: Session,
    *,
    phone: str,
    full_name: str,
    role: UserRole,
    subcity: str,
) -> None:
    normalized_phone = normalize_phone(phone)
    normalized_subcity = enforce_addis_subcity(subcity)
    otp = generate_otp()
    otp_hash = hash_otp(otp)
    now = datetime.utcnow()
    redis_client = _get_redis_client()

    if redis_client:
        rl_key = f"auth:otp:rl:{normalized_phone}"
        otp_key = f"auth:otp:{normalized_phone}"
        count = redis_client.incr(rl_key)
        if count == 1:
            redis_client.expire(rl_key, _otp_rate_limit_window_seconds())
        if count > _otp_rate_limit_max_requests():
            raise HTTPException(status_code=429, detail="Too many OTP requests. Try again later.")
        redis_client.setex(
            otp_key,
            _otp_ttl_seconds(),
            json.dumps(
                {
                    "phone": normalized_phone,
                    "full_name": full_name.strip(),
                    "role": role.value,
                    "subcity": normalized_subcity,
                    "otp_hash": otp_hash,
                    "requested_at": now.isoformat(),
                }
            ),
        )
    else:
        window_start = now - timedelta(seconds=_otp_rate_limit_window_seconds())
        recent_count = db.execute(
            select(func.count(OtpRequestLog.id)).where(
                OtpRequestLog.phone == normalized_phone,
                OtpRequestLog.created_at >= window_start,
            )
        ).scalar_one()
        if recent_count >= _otp_rate_limit_max_requests():
            raise HTTPException(status_code=429, detail="Too many OTP requests. Try again later.")

        db.add(OtpRequestLog(phone=normalized_phone))
        db.add(
            OtpChallenge(
                phone=normalized_phone,
                full_name=full_name.strip(),
                role=role,
                subcity=normalized_subcity,
                otp_hash=otp_hash,
                expires_at=now + timedelta(seconds=_otp_ttl_seconds()),
            )
        )
        db.commit()

    if _is_dev_mode():
        logger.info("DEV OTP phone=%s otp=%s", normalized_phone, otp)


def verify_otp_and_issue_token(db: Session, *, phone: str, otp: str) -> str:
    normalized_phone = normalize_phone(phone)
    provided_hash = hash_otp(otp.strip())
    now = datetime.utcnow()
    redis_client = _get_redis_client()

    otp_payload = None
    if redis_client:
        otp_key = f"auth:otp:{normalized_phone}"
        raw = redis_client.get(otp_key)
        if not raw:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        otp_payload = json.loads(raw)
        if not hmac.compare_digest(provided_hash, otp_payload["otp_hash"]):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        redis_client.delete(otp_key)
    else:
        challenge = db.execute(
            select(OtpChallenge)
            .where(
                OtpChallenge.phone == normalized_phone,
                OtpChallenge.consumed_at.is_(None),
                OtpChallenge.expires_at >= now,
            )
            .order_by(OtpChallenge.created_at.desc())
            .with_for_update()
        ).scalar_one_or_none()
        if not challenge:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        if not hmac.compare_digest(provided_hash, challenge.otp_hash):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        otp_payload = {
            "phone": challenge.phone,
            "full_name": challenge.full_name,
            "role": challenge.role.value,
            "subcity": challenge.subcity,
            "challenge_id": challenge.id,
        }

    role = UserRole(otp_payload["role"])
    subcity = enforce_addis_subcity(otp_payload["subcity"])
    user = db.execute(select(User).where(User.phone == normalized_phone).with_for_update()).scalar_one_or_none()
    if user:
        if user.is_banned:
            raise HTTPException(status_code=403, detail="User is banned")
        if user.role != role:
            raise HTTPException(status_code=400, detail="Role mismatch for existing user")
        user.full_name = otp_payload["full_name"]
        user.subcity = subcity
    else:
        user = User(
            role=role,
            full_name=otp_payload["full_name"],
            phone=normalized_phone,
            subcity=subcity,
            is_banned=False,
        )
        db.add(user)
        db.flush()

    if not redis_client:
        challenge_to_consume = db.get(OtpChallenge, otp_payload["challenge_id"])
        challenge_to_consume.consumed_at = now
    db.commit()
    return create_access_token(user_id=user.id, role=user.role)


def create_access_token(*, user_id: int, role: UserRole) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=_jwt_exp_minutes())).timestamp()),
    }
    header = {"alg": _jwt_algorithm(), "typ": "JWT"}
    header_segment = _b64url_encode_json(header)
    payload_segment = _b64url_encode_json(payload)
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _b64url_encode_bytes(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def decode_access_token(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    header_segment, payload_segment, signature_segment = parts
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_sig = hmac.new(_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_sig_segment = _b64url_encode_bytes(expected_sig)
    if not hmac.compare_digest(signature_segment, expected_sig_segment):
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    try:
        header = _b64url_decode_json(header_segment)
        payload = _b64url_decode_json(payload_segment)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    if header.get("alg") != _jwt_algorithm() or header.get("typ") != "JWT":
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(datetime.utcnow().timestamp()):
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    return payload


def _b64url_encode_bytes(value: bytes) -> str:
    return urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64url_encode_json(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64url_encode_bytes(raw)


def _b64url_decode_json(value: str) -> dict:
    padding = "=" * (-len(value) % 4)
    decoded = urlsafe_b64decode((value + padding).encode("utf-8"))
    return json.loads(decoded.decode("utf-8"))
