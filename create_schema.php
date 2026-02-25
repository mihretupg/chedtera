<?php

declare(strict_types=1);

/**
 * Usage:
 *   DB_HOST=localhost DB_PORT=5432 DB_NAME=chedtera DB_USER=postgres DB_PASS=postgres php create_schema.php
 */

$dbHost = getenv('DB_HOST') ?: 'localhost';
$dbPort = getenv('DB_PORT') ?: '5432';
$dbName = getenv('DB_NAME') ?: 'chedtera';
$dbUser = getenv('DB_USER') ?: 'postgres';
$dbPass = getenv('DB_PASS') ?: 'postgres';

$dsn = sprintf('pgsql:host=%s;port=%s;dbname=%s', $dbHost, $dbPort, $dbName);

try {
    $pdo = new PDO($dsn, $dbUser, $dbPass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);

    $sql = <<<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'listing_status') THEN
        CREATE TYPE listing_status AS ENUM ('draft','published','sold','archived','hidden');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS users (
  id               BIGSERIAL PRIMARY KEY,
  phone            TEXT NOT NULL UNIQUE,
  full_name        TEXT,
  subcity          TEXT NOT NULL,
  role             TEXT NOT NULL DEFAULT 'user',
  is_banned        BOOLEAN NOT NULL DEFAULT FALSE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS otp_requests (
  id               BIGSERIAL PRIMARY KEY,
  phone            TEXT NOT NULL,
  code_hash        TEXT NOT NULL,
  expires_at       TIMESTAMPTZ NOT NULL,
  attempts         INT NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS categories (
  id               BIGSERIAL PRIMARY KEY,
  name             TEXT NOT NULL UNIQUE,
  is_active        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS subcities (
  id               BIGSERIAL PRIMARY KEY,
  name             TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS listings (
  id               BIGSERIAL PRIMARY KEY,
  seller_id        BIGINT NOT NULL REFERENCES users(id),
  category_id      BIGINT NOT NULL REFERENCES categories(id),
  title            TEXT NOT NULL,
  description      TEXT,
  price_birr       BIGINT NOT NULL,
  condition        TEXT,
  subcity          TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'draft',
  is_deleted       BOOLEAN NOT NULL DEFAULT FALSE,
  published_at     TIMESTAMPTZ,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_listings_status CHECK (status IN ('draft','published','sold','archived','hidden'))
);

CREATE INDEX IF NOT EXISTS idx_listings_category ON listings(category_id);
CREATE INDEX IF NOT EXISTS idx_listings_seller   ON listings(seller_id);
CREATE INDEX IF NOT EXISTS idx_listings_status   ON listings(status);
CREATE INDEX IF NOT EXISTS idx_listings_subcity  ON listings(subcity);

CREATE TABLE IF NOT EXISTS listing_images (
  id               BIGSERIAL PRIMARY KEY,
  listing_id       BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  url              TEXT NOT NULL,
  sort_order       INT NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS plan_catalog (
  id               BIGSERIAL PRIMARY KEY,
  name             TEXT NOT NULL UNIQUE,
  max_listings     INT NOT NULL,
  price_birr       INT NOT NULL,
  duration_days    INT NOT NULL DEFAULT 30,
  is_active        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS seller_plans (
  id               BIGSERIAL PRIMARY KEY,
  seller_id        BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  plan_catalog_id  BIGINT NOT NULL REFERENCES plan_catalog(id),
  max_listings     INT NOT NULL,
  price_birr       INT NOT NULL,
  starts_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at       TIMESTAMPTZ NOT NULL,
  is_active        BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS seller_plan_history (
  id               BIGSERIAL PRIMARY KEY,
  seller_id        BIGINT NOT NULL REFERENCES users(id),
  plan_catalog_id  BIGINT NOT NULL REFERENCES plan_catalog(id),
  max_listings     INT NOT NULL,
  price_birr       INT NOT NULL,
  starts_at        TIMESTAMPTZ NOT NULL,
  expires_at       TIMESTAMPTZ NOT NULL,
  payment_id       BIGINT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS credit_packages (
  id               BIGSERIAL PRIMARY KEY,
  category_id      BIGINT NOT NULL REFERENCES categories(id),
  name             TEXT NOT NULL,
  credits          INT NOT NULL,
  price_birr       INT NOT NULL,
  is_active        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS buyer_credit_wallet (
  id               BIGSERIAL PRIMARY KEY,
  buyer_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id      BIGINT NOT NULL REFERENCES categories(id),
  total_credits    INT NOT NULL DEFAULT 0,
  used_credits     INT NOT NULL DEFAULT 0,
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (buyer_id, category_id)
);

CREATE TABLE IF NOT EXISTS credit_unlocks (
  id               BIGSERIAL PRIMARY KEY,
  buyer_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  seller_id        BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id      BIGINT NOT NULL REFERENCES categories(id),
  listing_id       BIGINT REFERENCES listings(id),
  unlocked_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (buyer_id, seller_id, category_id)
);

CREATE TABLE IF NOT EXISTS conversations (
  id               BIGSERIAL PRIMARY KEY,
  listing_id       BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  buyer_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  seller_id        BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (listing_id, buyer_id, seller_id)
);

CREATE TABLE IF NOT EXISTS messages (
  id               BIGSERIAL PRIMARY KEY,
  conversation_id  BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  sender_id        BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body             TEXT NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS payments (
  id               BIGSERIAL PRIMARY KEY,
  user_id          BIGINT NOT NULL REFERENCES users(id),
  payment_type     TEXT NOT NULL,
  status           TEXT NOT NULL,
  amount_birr      INT NOT NULL,
  provider         TEXT NOT NULL,
  provider_ref     TEXT NOT NULL,
  metadata         JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  confirmed_at     TIMESTAMPTZ,
  UNIQUE (provider, provider_ref)
);

CREATE TABLE IF NOT EXISTS purchases (
  id               BIGSERIAL PRIMARY KEY,
  payment_id       BIGINT NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
  buyer_id         BIGINT REFERENCES users(id),
  seller_id        BIGINT REFERENCES users(id),
  category_id      BIGINT REFERENCES categories(id),
  credit_package_id BIGINT REFERENCES credit_packages(id),
  plan_catalog_id  BIGINT REFERENCES plan_catalog(id),
  applied          BOOLEAN NOT NULL DEFAULT FALSE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
  id               BIGSERIAL PRIMARY KEY,
  reporter_id      BIGINT REFERENCES users(id),
  listing_id       BIGINT REFERENCES listings(id),
  reported_user_id BIGINT REFERENCES users(id),
  reason           TEXT NOT NULL,
  details          TEXT,
  status           TEXT NOT NULL DEFAULT 'open',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS admin_actions (
  id               BIGSERIAL PRIMARY KEY,
  admin_id         BIGINT NOT NULL REFERENCES users(id),
  action           TEXT NOT NULL,
  target_type      TEXT NOT NULL,
  target_id        BIGINT NOT NULL,
  notes            TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL;

    $pdo->beginTransaction();
    $pdo->exec($sql);
    $pdo->commit();

    echo "Schema created successfully.\n";
} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    fwrite(STDERR, "Failed to create schema: " . $e->getMessage() . PHP_EOL);
    exit(1);
}

