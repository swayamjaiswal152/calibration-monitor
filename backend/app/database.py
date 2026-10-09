import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/calibration")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Sync URL for Worker, Async URL for API. Pin explicit drivers so resolution
# is deterministic across SQLAlchemy versions (2.1+ defaults postgresql:// to
# psycopg v3, which this project does not install — it uses psycopg2/asyncpg).
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://") if "postgresql://" in DATABASE_URL else DATABASE_URL
_sync_base = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
SYNC_DATABASE_URL = (
    _sync_base.replace("postgresql://", "postgresql+psycopg2://", 1)
    if _sync_base.startswith("postgresql://")
    else _sync_base
)

# For API - Async
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# For Worker - Sync
sync_engine = create_engine(SYNC_DATABASE_URL, pool_size=10, max_overflow=20)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session