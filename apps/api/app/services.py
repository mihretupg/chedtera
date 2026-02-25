from contextlib import contextmanager
from dataclasses import dataclass
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .locations import enforce_addis_subcity
from .models import (
    BuyerCreditBalance,
    Listing,
    ListingUnlock,
    PaymentEvent,
    PaymentType,
    SellerCapacityBalance,
    User,
    UserRole,
)
from .pricing import (
    BUYER_CONTACT_PACKAGE_PRICE_BIRR,
    BUYER_CONTACT_PACKAGE_SIZE,
    seller_capacity_price_birr,
)


@dataclass
class PurchaseResult:
    amount_birr: int
    applied: bool
    balance_after: int


@dataclass
class UnlockResult:
    listing_id: int
    buyer_id: int
    contact_unlocked: bool
    seller_phone: str
    chat_allowed: bool


def _require_role(user: User, role: UserRole) -> None:
    if user.role != role:
        raise HTTPException(status_code=403, detail=f"Operation requires {role.value} role")


@contextmanager
def _transaction_scope(db: Session):
    tx = db.begin_nested() if db.in_transaction() else db.begin()
    with tx:
        yield


def purchase_buyer_credits(db: Session, buyer: User, category: str, idempotency_key: str) -> PurchaseResult:
    _require_role(buyer, UserRole.BUYER)

    with _transaction_scope(db):
        existing = db.get(PaymentEvent, idempotency_key)
        if existing:
            balance = db.execute(
                select(BuyerCreditBalance).where(
                    BuyerCreditBalance.buyer_id == buyer.id,
                    BuyerCreditBalance.category == category,
                )
            ).scalar_one()
            return PurchaseResult(
                amount_birr=existing.amount_birr,
                applied=False,
                balance_after=balance.contacts_remaining,
            )

        balance = db.execute(
            select(BuyerCreditBalance)
            .where(BuyerCreditBalance.buyer_id == buyer.id, BuyerCreditBalance.category == category)
            .with_for_update()
        ).scalar_one_or_none()

        if not balance:
            balance = BuyerCreditBalance(
                buyer_id=buyer.id,
                category=category,
                contacts_remaining=0,
            )
            db.add(balance)
            db.flush()

        balance.contacts_remaining += BUYER_CONTACT_PACKAGE_SIZE

        event = PaymentEvent(
            idempotency_key=idempotency_key,
            user_id=buyer.id,
            payment_type=PaymentType.BUYER_CREDIT,
            amount_birr=BUYER_CONTACT_PACKAGE_PRICE_BIRR,
            metadata_json=json.dumps({"category": category, "contacts": BUYER_CONTACT_PACKAGE_SIZE}),
        )
        db.add(event)

        return PurchaseResult(
            amount_birr=BUYER_CONTACT_PACKAGE_PRICE_BIRR,
            applied=True,
            balance_after=balance.contacts_remaining,
        )


def purchase_seller_capacity(db: Session, seller: User, slots: int, idempotency_key: str) -> PurchaseResult:
    _require_role(seller, UserRole.SELLER)

    amount_birr = seller_capacity_price_birr(slots)
    with _transaction_scope(db):
        existing = db.get(PaymentEvent, idempotency_key)
        if existing:
            capacity = db.execute(
                select(SellerCapacityBalance).where(SellerCapacityBalance.seller_id == seller.id)
            ).scalar_one()
            return PurchaseResult(
                amount_birr=existing.amount_birr,
                applied=False,
                balance_after=capacity.slots_remaining,
            )

        capacity = db.execute(
            select(SellerCapacityBalance).where(SellerCapacityBalance.seller_id == seller.id).with_for_update()
        ).scalar_one_or_none()

        if not capacity:
            capacity = SellerCapacityBalance(seller_id=seller.id, slots_remaining=0)
            db.add(capacity)
            db.flush()

        capacity.slots_remaining += slots

        event = PaymentEvent(
            idempotency_key=idempotency_key,
            user_id=seller.id,
            payment_type=PaymentType.SELLER_CAPACITY,
            amount_birr=amount_birr,
            metadata_json=json.dumps({"slots": slots}),
        )
        db.add(event)

        return PurchaseResult(amount_birr=amount_birr, applied=True, balance_after=capacity.slots_remaining)


def create_listing(db: Session, seller: User, *, title: str, category: str, subcity: str, price_birr: int, description: str) -> Listing:
    _require_role(seller, UserRole.SELLER)
    normalized_subcity = enforce_addis_subcity(subcity)

    listing = Listing(
        seller_id=seller.id,
        title=title,
        category=category.strip(),
        subcity=normalized_subcity,
        price_birr=price_birr,
        description=description,
        is_published=False,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def publish_listing(db: Session, seller: User, listing_id: int) -> Listing:
    _require_role(seller, UserRole.SELLER)

    with _transaction_scope(db):
        listing = db.execute(select(Listing).where(Listing.id == listing_id).with_for_update()).scalar_one_or_none()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        if listing.seller_id != seller.id:
            raise HTTPException(status_code=403, detail="You can only publish your own listings")
        if listing.is_published:
            raise HTTPException(status_code=400, detail="Listing already published")

        capacity = db.execute(
            select(SellerCapacityBalance).where(SellerCapacityBalance.seller_id == seller.id).with_for_update()
        ).scalar_one_or_none()
        if not capacity or capacity.slots_remaining < 1:
            raise HTTPException(status_code=402, detail="Insufficient listing capacity")

        capacity.slots_remaining -= 1
        listing.is_published = True

    db.refresh(listing)
    return listing


def unlock_listing_contact(db: Session, buyer: User, listing_id: int) -> UnlockResult:
    _require_role(buyer, UserRole.BUYER)

    with _transaction_scope(db):
        listing = db.execute(select(Listing).where(Listing.id == listing_id).with_for_update()).scalar_one_or_none()
        if not listing or not listing.is_published:
            raise HTTPException(status_code=404, detail="Published listing not found")

        existing_unlock = db.execute(
            select(ListingUnlock)
            .where(ListingUnlock.buyer_id == buyer.id, ListingUnlock.listing_id == listing_id)
            .with_for_update()
        ).scalar_one_or_none()
        seller = db.execute(select(User).where(User.id == listing.seller_id)).scalar_one()

        if existing_unlock:
            return UnlockResult(
                listing_id=listing.id,
                buyer_id=buyer.id,
                contact_unlocked=True,
                seller_phone=seller.phone,
                chat_allowed=True,
            )

        balance = db.execute(
            select(BuyerCreditBalance)
            .where(BuyerCreditBalance.buyer_id == buyer.id, BuyerCreditBalance.category == listing.category)
            .with_for_update()
        ).scalar_one_or_none()

        if not balance or balance.contacts_remaining < 1:
            raise HTTPException(status_code=402, detail="Insufficient contact credits")

        balance.contacts_remaining -= 1
        unlock = ListingUnlock(buyer_id=buyer.id, listing_id=listing.id)
        db.add(unlock)

        return UnlockResult(
            listing_id=listing.id,
            buyer_id=buyer.id,
            contact_unlocked=True,
            seller_phone=seller.phone,
            chat_allowed=True,
        )


def has_chat_access(db: Session, buyer: User, listing_id: int) -> bool:
    _require_role(buyer, UserRole.BUYER)

    unlock = db.execute(
        select(ListingUnlock).where(ListingUnlock.buyer_id == buyer.id, ListingUnlock.listing_id == listing_id)
    ).scalar_one_or_none()
    return unlock is not None
