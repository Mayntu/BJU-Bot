from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD "timezone" VARCHAR(64) NOT NULL DEFAULT 'UTC';
        CREATE TABLE IF NOT EXISTS "user_daily_meals" (
    "id" UUID NOT NULL PRIMARY KEY,
    "date" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "calories" DOUBLE PRECISION NOT NULL,
    "order" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_user_daily__user_id_afe428" ON "user_daily_meals" ("user_id", "date");
        ALTER TABLE "user_daily_reports" ADD "meal_name" VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" DROP COLUMN "timezone";
        ALTER TABLE "user_daily_reports" DROP COLUMN "meal_name";
        DROP TABLE IF EXISTS "user_daily_meals";"""
