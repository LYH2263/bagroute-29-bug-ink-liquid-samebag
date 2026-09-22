from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.pack_engine import CATEGORY_NORMAL
from app.services.seed import seed_if_empty


def ensure_columns() -> None:
    """幂等补列：旧库缺少 category 列时自动添加（create_all 不会改已有表）。"""
    ddl = [
        f"ALTER TABLE subscriber_stops ADD COLUMN IF NOT EXISTS category VARCHAR(16) NOT NULL DEFAULT '{CATEGORY_NORMAL}'",
        f"ALTER TABLE bag_items ADD COLUMN IF NOT EXISTS category VARCHAR(16) NOT NULL DEFAULT '{CATEGORY_NORMAL}'",
        f"ALTER TABLE reject_records ADD COLUMN IF NOT EXISTS category VARCHAR(16) NOT NULL DEFAULT '{CATEGORY_NORMAL}'",
    ]
    with engine.begin() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    if settings.seed_on_empty:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title="BagRoute", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
