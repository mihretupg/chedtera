import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class UserRole(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class BuyerCreditBalance(Base):
    __tablename__ = "buyer_credit_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    contacts_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("buyer_id", "category", name="uq_buyer_category"),)


class SellerCapacityBalance(Base):
    __tablename__ = "seller_capacity_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    slots_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subcity: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    price_birr: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    seller: Mapped["User"] = relationship("User")


class ListingUnlock(Base):
    __tablename__ = "listing_unlocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("buyer_id", "listing_id", name="uq_buyer_listing_unlock"),)


class PaymentType(str, enum.Enum):
    BUYER_CREDIT = "buyer_credit"
    SELLER_CAPACITY = "seller_capacity"


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    idempotency_key: Mapped[str] = mapped_column(String(120), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    amount_birr: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
