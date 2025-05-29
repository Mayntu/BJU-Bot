from openai import AsyncOpenAI
from bot.config import OPENAI_KEY

client = AsyncOpenAI(api_key=OPENAI_KEY)