from tortoise import Tortoise

from bot.config import DB_URL

async def init_db():
    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": ["db.models"]}
    )
    await Tortoise.generate_schemas()
