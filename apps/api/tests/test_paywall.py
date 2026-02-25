from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import BuyerCreditBalance, Listing, ListingUnlock, PaymentEvent, SellerCapacityBalance, User, UserRole
from app.schemas import ListingResponse
from app.services import (
    create_listing,
    publish_listing,
    purchase_buyer_credits,
    purchase_seller_capacity,
    unlock_listing_contact,
)


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def test_buyer_credit_purchase_is_idempotent():
    db = make_session()
    buyer = User(id=10, role=UserRole.BUYER, full_name="Buyer A", phone="+251900000001", subcity="bole")
    db.add(buyer)
    db.commit()

    first = purchase_buyer_credits(db, buyer, "Beds", "pay-1")
    second = purchase_buyer_credits(db, buyer, "Beds", "pay-1")

    balance = db.execute(
        select(BuyerCreditBalance).where(BuyerCreditBalance.buyer_id == buyer.id, BuyerCreditBalance.category == "Beds")
    ).scalar_one()
    events = db.execute(select(PaymentEvent).where(PaymentEvent.idempotency_key == "pay-1")).scalars().all()

    assert first.applied is True
    assert second.applied is False
    assert balance.contacts_remaining == 10
    assert len(events) == 1


def test_unlock_deducts_once_and_returns_phone():
    db = make_session()
    seller = User(id=20, role=UserRole.SELLER, full_name="Seller", phone="+251911111111", subcity="yeka")
    buyer = User(id=21, role=UserRole.BUYER, full_name="Buyer", phone="+251922222222", subcity="bole")
    db.add_all([seller, buyer])
    db.commit()

    purchase_seller_capacity(db, seller, 1, "seller-pay-1")
    listing = create_listing(
        db,
        seller,
        title="Bed frame",
        category="Beds",
        subcity="Bole",
        price_birr=12000,
        description="Solid wood bed frame",
    )
    publish_listing(db, seller, listing.id)

    purchase_buyer_credits(db, buyer, "Beds", "buyer-pay-1")

    first_unlock = unlock_listing_contact(db, buyer, listing.id)
    second_unlock = unlock_listing_contact(db, buyer, listing.id)

    balance = db.execute(
        select(BuyerCreditBalance).where(BuyerCreditBalance.buyer_id == buyer.id, BuyerCreditBalance.category == "Beds")
    ).scalar_one()
    unlocks = db.execute(
        select(ListingUnlock).where(ListingUnlock.buyer_id == buyer.id, ListingUnlock.listing_id == listing.id)
    ).scalars().all()

    assert first_unlock.chat_allowed is True
    assert second_unlock.chat_allowed is True
    assert first_unlock.seller_phone == "+251911111111"
    assert balance.contacts_remaining == 9
    assert len(unlocks) == 1


def test_publish_requires_capacity_and_deducts_slot():
    db = make_session()
    seller = User(id=30, role=UserRole.SELLER, full_name="Seller", phone="+251933333333", subcity="arada")
    db.add(seller)
    db.commit()

    purchase_seller_capacity(db, seller, 1, "seller-pay-2")
    listing = create_listing(
        db,
        seller,
        title="Sofa",
        category="Living",
        subcity="Yeka",
        price_birr=14000,
        description="Clean sofa set",
    )

    publish_listing(db, seller, listing.id)

    capacity = db.execute(select(SellerCapacityBalance).where(SellerCapacityBalance.seller_id == seller.id)).scalar_one()
    listing_db = db.execute(select(Listing).where(Listing.id == listing.id)).scalar_one()

    assert capacity.slots_remaining == 0
    assert listing_db.is_published is True


def test_public_payload_does_not_expose_phone():
    db = make_session()
    seller = User(id=40, role=UserRole.SELLER, full_name="Seller", phone="+251944444444", subcity="kirkos")
    db.add(seller)
    db.commit()

    purchase_seller_capacity(db, seller, 1, "seller-pay-3")
    listing = create_listing(
        db,
        seller,
        title="Wardrobe",
        category="Storage",
        subcity="Arada",
        price_birr=9000,
        description="Two-door wardrobe",
    )
    publish_listing(db, seller, listing.id)

    public_payload = ListingResponse.model_validate(listing).model_dump()
    assert "seller_phone" not in public_payload
    assert "phone" not in public_payload


def test_addis_only_subcity_validation():
    db = make_session()
    seller = User(id=50, role=UserRole.SELLER, full_name="Seller", phone="+251955555555", subcity="lideta")
    db.add(seller)
    db.commit()

    try:
        create_listing(
            db,
            seller,
            title="Desk",
            category="Office",
            subcity="Adama",
            price_birr=5000,
            description="Office desk",
        )
        raised = False
    except HTTPException as exc:
        assert exc.status_code == 400
        raised = True

    assert raised is True
