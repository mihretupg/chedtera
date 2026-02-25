from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import request_otp, verify_otp_and_issue_token
from .db import Base, engine, get_db
from .deps import get_current_user
from .schemas import (
    AuthRequestOtpRequest,
    AuthRequestOtpResponse,
    AuthTokenResponse,
    AuthVerifyOtpRequest,
    BuyerCreditPurchaseRequest,
    ChatAccessResponse,
    HealthResponse,
    ListingCreate,
    ListingUpdate,
    ListingResponse,
    MeResponse,
    PurchaseResponse,
    SellerCapacityPurchaseRequest,
    UnlockResponse,
)
from .services import (
    create_listing,
    get_published_listing,
    has_chat_access,
    list_published_listings,
    publish_listing,
    purchase_buyer_credits,
    purchase_seller_capacity,
    update_listing,
    unlock_listing_contact,
)

app = FastAPI(title="Chedtera API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/auth/request-otp", response_model=AuthRequestOtpResponse)
def request_otp_route(payload: AuthRequestOtpRequest, db: Session = Depends(get_db)) -> AuthRequestOtpResponse:
    request_otp(
        db,
        phone=payload.phone,
        full_name=payload.full_name,
        role=payload.role,
        subcity=payload.subcity,
    )
    return AuthRequestOtpResponse(detail="OTP sent")


@app.post("/auth/verify-otp", response_model=AuthTokenResponse)
def verify_otp_route(payload: AuthVerifyOtpRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    token = verify_otp_and_issue_token(db, phone=payload.phone, otp=payload.otp)
    return AuthTokenResponse(access_token=token)


@app.get("/me", response_model=MeResponse)
def get_me(user=Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=user.id,
        role=user.role,
        full_name=user.full_name,
        phone=user.phone,
        subcity=user.subcity,
        is_banned=user.is_banned,
    )


@app.post("/payments/buyer-credits", response_model=PurchaseResponse)
def buy_buyer_credits(
    payload: BuyerCreditPurchaseRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> PurchaseResponse:
    result = purchase_buyer_credits(db, user, payload.category.strip(), payload.idempotency_key)
    return PurchaseResponse(amount_birr=result.amount_birr, applied=result.applied, balance_after=result.balance_after)


@app.post("/payments/seller-capacity", response_model=PurchaseResponse)
def buy_seller_capacity(
    payload: SellerCapacityPurchaseRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> PurchaseResponse:
    result = purchase_seller_capacity(db, user, payload.slots, payload.idempotency_key)
    return PurchaseResponse(amount_birr=result.amount_birr, applied=result.applied, balance_after=result.balance_after)


@app.post("/listings", response_model=ListingResponse)
def create_listing_route(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> ListingResponse:
    listing = create_listing(
        db,
        user,
        title=payload.title,
        category=payload.category,
        subcity=payload.subcity,
        price_birr=payload.price_birr,
        description=payload.description,
    )
    return ListingResponse.model_validate(listing)


@app.patch("/listings/{listing_id}", response_model=ListingResponse)
def update_listing_route(
    listing_id: int,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> ListingResponse:
    listing = update_listing(
        db,
        user,
        listing_id,
        title=payload.title,
        category=payload.category,
        subcity=payload.subcity,
        price_birr=payload.price_birr,
        description=payload.description,
    )
    return ListingResponse.model_validate(listing)


@app.post("/listings/{listing_id}/publish", response_model=ListingResponse)
def publish_listing_route(
    listing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> ListingResponse:
    listing = publish_listing(db, user, listing_id)
    return ListingResponse.model_validate(listing)


@app.get("/listings", response_model=list[ListingResponse])
def get_listings(
    category: str | None = Query(default=None),
    subcity: str | None = Query(default=None),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ListingResponse]:
    listings = list_published_listings(
        db,
        category=category,
        subcity=subcity,
        min_price=min_price,
        max_price=max_price,
        keyword=keyword,
    )
    return [ListingResponse.model_validate(listing) for listing in listings]


@app.get("/listings/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)) -> ListingResponse:
    listing = get_published_listing(db, listing_id)
    return ListingResponse.model_validate(listing)


@app.post("/listings/{listing_id}/unlock", response_model=UnlockResponse)
def unlock_contact(
    listing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> UnlockResponse:
    result = unlock_listing_contact(db, user, listing_id)
    return UnlockResponse(
        listing_id=result.listing_id,
        buyer_id=result.buyer_id,
        contact_unlocked=result.contact_unlocked,
        seller_phone=result.seller_phone,
        chat_allowed=result.chat_allowed,
    )


@app.get("/listings/{listing_id}/chat-access", response_model=ChatAccessResponse)
def chat_access(
    listing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> ChatAccessResponse:
    allowed = has_chat_access(db, user, listing_id)
    return ChatAccessResponse(listing_id=listing_id, buyer_id=user.id, chat_allowed=allowed)
