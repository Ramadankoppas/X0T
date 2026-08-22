import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import redis.asyncio as redis

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://x0t_user:x0t_password@localhost:5432/x0t_db"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session