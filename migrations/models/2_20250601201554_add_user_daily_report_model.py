from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user_daily_reports" (
    "id" UUID NOT NULL PRIMARY KEY,
    "date" TIMESTAMPTZ NOT NULL,
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
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "user_daily_reports";"""
