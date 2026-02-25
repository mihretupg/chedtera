from typing import Any

from pydantic import BaseModel, Field

from .models import UserRole


class HealthResponse(BaseModel):
    status: str = "ok"


class ListingCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    category: str = Field(min_length=2, max_length=64)
    subcity: str = Field(min_length=2, max_length=64)
    price_birr: int = Field(gt=0)
    description: str = Field(min_length=5, max_length=2000)


class ListingResponse(BaseModel):
    id: int
    seller_id: int
    title: str
    category: str
    subcity: str
    price_birr: int
    description: str
    is_published: bool

    model_config = {"from_attributes": True}


class BuyerCreditPurchaseRequest(BaseModel):
    category: str = Field(min_length=2, max_length=64)
    idempotency_key: str = Field(min_length=4, max_length=120)


class SellerCapacityPurchaseRequest(BaseModel):
    slots: int = Field(gt=0)
    idempotency_key: str = Field(min_length=4, max_length=120)


class PurchaseResponse(BaseModel):
    amount_birr: int
    applied: bool
    balance_after: int


class UnlockResponse(BaseModel):
    listing_id: int
    buyer_id: int
    contact_unlocked: bool
    seller_phone: str
    chat_allowed: bool


class ChatAccessResponse(BaseModel):
    listing_id: int
    buyer_id: int
    chat_allowed: bool


class ErrorResponse(BaseModel):
    detail: Any


class AuthRequestOtpRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=32)
    full_name: str = Field(min_length=2, max_length=120)
    role: UserRole
    subcity: str = Field(min_length=2, max_length=64)


class AuthRequestOtpResponse(BaseModel):
    detail: str


class AuthVerifyOtpRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=32)
    otp: str = Field(min_length=4, max_length=12)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    role: UserRole
    full_name: str
    phone: str
    subcity: str
    is_banned: bool
