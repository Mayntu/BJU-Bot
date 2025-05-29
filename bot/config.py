import os
from dotenv import load_dotenv

load_dotenv()

# from pydantic import BaseSettings

# class Settings(BaseSettings):
#     BOT_TOKEN: str
#     DATABASE_URL: str
#     OPENAI_KEY: str

#     class Config:
#         env_file = ".env"

# settings : Settings = Settings()


BOT_TOKEN : str = os.getenv("BOT_TOKEN")
OPENAI_KEY : str = os.getenv("OPENAI_KEY")
DB_URL : str = os.getenv("DATABASE_URL")
MAX_TOKENS : str = os.getenv("MAX_TOKENS", 1000)

TORTOISE_ORM = {
    "connections": {
        "default": DB_URL
    },
    "apps": {
        "models": {
            "models": ["db.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
