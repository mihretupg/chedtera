from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import decode_access_token
from .db import get_db
from .locations import enforce_addis_subcity
from .models import User, UserRole


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_user_id: int | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
    x_user_phone: str | None = Header(default=None),
    x_user_subcity: str | None = Header(default=None),
) -> User:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="Authorization header must use Bearer token")
        claims = decode_access_token(token)
        user_id_raw = claims.get("sub")
        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="Invalid authentication token") from exc
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found for token")
        if user.is_banned:
            raise HTTPException(status_code=403, detail="User is banned")
        return user

    if x_user_id is None or x_user_role is None:
        raise HTTPException(status_code=401, detail="Missing auth headers: x-user-id and x-user-role")

    try:
        role = UserRole(x_user_role.lower())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="x-user-role must be buyer or seller") from exc

    user = db.execute(select(User).where(User.id == x_user_id)).scalar_one_or_none()
    if user:
        if user.role != role:
            raise HTTPException(status_code=403, detail="Role mismatch for user")
        if user.is_banned:
            raise HTTPException(status_code=403, detail="User is banned")
        return user

    if not x_user_name or not x_user_phone or not x_user_subcity:
        raise HTTPException(status_code=400, detail="x-user-name, x-user-phone, and x-user-subcity required for new users")

    try:
        normalized_subcity = enforce_addis_subcity(x_user_subcity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = User(
        id=x_user_id,
        role=role,
        full_name=x_user_name.strip(),
        phone=x_user_phone.strip(),
        subcity=normalized_subcity,
        is_banned=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
