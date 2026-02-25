from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, UserRole


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
    x_user_phone: str | None = Header(default=None),
) -> User:
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
        return user

    if not x_user_name or not x_user_phone:
        raise HTTPException(status_code=400, detail="x-user-name and x-user-phone required for new users")

    user = User(id=x_user_id, role=role, full_name=x_user_name.strip(), phone=x_user_phone.strip())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
