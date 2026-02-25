# AGENTS.md

## Non-negotiable Engineering Rules

1. Use database transactions for all unlock and publish flows. Never split paywall state changes across non-transactional operations.
2. All payment write paths must be idempotent and keyed by a unique idempotency key.
3. Never expose seller phone numbers in public listing/feed endpoints. Seller phone may only be returned after a successful unlock.
4. Addis-only marketplace scope is enforced server-side. Listing subcity must be one of Addis Ababa subcities.
5. Critical paywall logic (credits, capacity, unlock, publish, phone privacy) requires automated tests before merge.

## Required Reviews

1. Validate transaction boundaries in service layer code.
2. Validate idempotency behavior for retries.
3. Validate phone privacy in API schemas and responses.
4. Validate Addis-only enforcement paths and error handling.
5. Validate and run tests for critical monetization logic.
