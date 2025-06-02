from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user_subscriptions" DROP CONSTRAINT IF EXISTS "uid_user_subscr_user_id_ea7936";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_user_subscr_user_id_ea7936" ON "user_subscriptions" ("user_id", "plan", "start_date");"""
