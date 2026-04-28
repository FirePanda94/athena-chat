import asyncpg
from src.config.index import appConfig

pool = None

async def connect_db():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(dsn=appConfig['database_url'])
    
async def disconnect_db():
    global pool
    if pool is not None:
        await pool.close()
        pool = None