BUYER_CONTACT_PACKAGE_SIZE = 10
BUYER_CONTACT_PACKAGE_PRICE_BIRR = 100


def seller_capacity_price_birr(slots: int) -> int:
    if slots <= 0:
        raise ValueError("Slots must be positive")
    if 1 <= slots <= 5:
        return 200
    if 6 <= slots <= 10:
        return 250
    return 500
