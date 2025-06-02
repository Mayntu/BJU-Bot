from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "telegram_id" BIGINT NOT NULL UNIQUE,
    "username" VARCHAR(255) NOT NULL UNIQUE,
    "timezone" VARCHAR(64) NOT NULL DEFAULT 'UTC',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "meals" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "total_weight" DOUBLE PRECISION NOT NULL,
    "total_calories" DOUBLE PRECISION NOT NULL,
    "total_protein" DOUBLE PRECISION NOT NULL,
    "total_fat" DOUBLE PRECISION NOT NULL,
    "total_carbs" DOUBLE PRECISION NOT NULL,
    "total_fiber" DOUBLE PRECISION NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "ingredients" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "weight" DOUBLE PRECISION NOT NULL,
    "calories" DOUBLE PRECISION NOT NULL,
    "protein" DOUBLE PRECISION NOT NULL,
    "fat" DOUBLE PRECISION NOT NULL,
    "carbs" DOUBLE PRECISION NOT NULL,
    "fiber" DOUBLE PRECISION NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "meal_id" UUID NOT NULL REFERENCES "meals" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "user_daily_meals" (
    "id" UUID NOT NULL PRIMARY KEY,
    "date" DATE NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "calories" DOUBLE PRECISION NOT NULL,
    "order" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_user_daily__user_id_afe428" ON "user_daily_meals" ("user_id", "date");
CREATE TABLE IF NOT EXISTS "user_daily_reports" (
    "id" UUID NOT NULL PRIMARY KEY,
    "date" DATE NOT NULL,
    "meal_name" VARCHAR(255),
    "total_weight" DOUBLE PRECISION NOT NULL,
    "total_calories" DOUBLE PRECISION NOT NULL,
    "total_protein" DOUBLE PRECISION NOT NULL,
    "total_fat" DOUBLE PRECISION NOT NULL,
    "total_carbs" DOUBLE PRECISION NOT NULL,
    "total_fiber" DOUBLE PRECISION NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_daily__user_id_c93729" UNIQUE ("user_id", "date")
);
CREATE TABLE IF NOT EXISTS "user_subscriptions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "plan" VARCHAR(32) NOT NULL,
    "price" DECIMAL(10,2) NOT NULL,
    "currency" VARCHAR(32) NOT NULL DEFAULT 'RUB',
    "start_date" DATE NOT NULL,
    "end_date" DATE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_subscr_user_id_ea7936" UNIQUE ("user_id", "plan", "start_date")
);
CREATE INDEX IF NOT EXISTS "idx_user_subscr_user_id_a6797b" ON "user_subscriptions" ("user_id", "plan");
CREATE TABLE IF NOT EXISTS "payments" (
    "id" UUID NOT NULL PRIMARY KEY,
    "status" VARCHAR(32) NOT NULL DEFAULT 'pending',
    "yookassa_payment_id" VARCHAR(64) UNIQUE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "user_subscription_id" UUID NOT NULL REFERENCES "user_subscriptions" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_payments_user_id_d6dc35" UNIQUE ("user_id", "created_at")
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
