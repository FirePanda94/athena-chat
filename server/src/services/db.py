import asyncpg
from src.config.index import appConfig

pool = None

async def connect_db():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            dsn=appConfig['database_url'] + "?sslmode=require",
            statement_cache_size=0
        )

async def disconnect_db():
    global pool
    if pool is not None:
        await pool.close()
        pool = None