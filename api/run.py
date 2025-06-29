from fastapi import FastAPI
from api.webhooks.yookassa import router as yookassa_router
from fastapi.middleware.cors import CORSMiddleware

from db.init import init_db
import db.signals # noqa

app = FastAPI()
app.include_router(yookassa_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def startup():
    await init_db()