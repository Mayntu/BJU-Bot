from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user_daily_meals" ALTER COLUMN "date" TYPE DATE USING "date"::DATE;
        ALTER TABLE "user_daily_reports" ALTER COLUMN "date" TYPE DATE USING "date"::DATE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user_daily_meals" ALTER COLUMN "date" TYPE TIMESTAMPTZ USING "date"::TIMESTAMPTZ;
        ALTER TABLE "user_daily_reports" ALTER COLUMN "date" TYPE TIMESTAMPTZ USING "date"::TIMESTAMPTZ;"""
