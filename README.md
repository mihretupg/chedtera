# Chedtera Monorepo

Addis-only marketplace monorepo with:

- `apps/api`: FastAPI + SQLAlchemy + PostgreSQL-backed paywall logic
- `apps/web`: React + Tailwind frontend

## Monetization Rules Implemented

- Buyer purchases category contact credits (`10 contacts = 100 birr` package).
- Seller purchases listing capacity by slot bracket:
  - `1-5 slots = 200 birr`
  - `6-10 slots = 250 birr`
  - `>10 slots = 500 birr`
- Chat/contact unlock is available only after buyer unlock.
- Seller phone is never exposed in public listing endpoints; returned only on unlock.
- Addis-only subcity validation is enforced server-side.

## Repo Structure

```text
apps/
  api/
    app/
    tests/
  web/
docker-compose.yml
AGENTS.md
```

## Run Locally with Docker

```bash
docker compose up --build
```

Open:

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Web: `http://localhost:5173`

To also run Redis:

```bash
docker compose --profile cache up --build
```

## Run API Locally (without Docker)

```bash
cd apps/api
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg://chedtera:chedtera@localhost:5432/chedtera"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## DB Migrations + Seed

Run from `apps/api`:

```bash
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
```

Optional shortcut (if `make` is available):

```bash
make migrate
make seed
```

Tables in initial migration include:

- users, categories, subcities (Addis only), listings, listing_images
- plan_catalog, seller_plans
- credit_packages, buyer_credit_wallet, credit_unlocks
- conversations, messages
- payments, purchases
- reports, admin_actions

## Run Web Locally (without Docker)

```bash
cd apps/web
npm install
npm run dev
```

## Test + Build Validation

Backend tests:

```bash
cd apps/api
py -3.13 -m pytest
```

Web production build:

```bash
cd apps/web
npm install
npm run build
```

## Minimal API Flow

1. Login in web page with headers-backed identity fields.
2. Seller buys capacity: `POST /payments/seller-capacity`.
3. Seller creates listing draft: `POST /listings`.
4. Seller publishes listing: `POST /listings/{id}/publish`.
5. Buyer buys credits: `POST /payments/buyer-credits`.
6. Buyer unlocks listing: `POST /listings/{id}/unlock` and receives seller phone.
