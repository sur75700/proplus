from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from settings import settings

db: AsyncIOMotorDatabase | None = None
_client: AsyncIOMotorClient | None = None


async def connect_db():
    global db, _client
    if db is not None:
        return
    _client = AsyncIOMotorClient(settings.MONGO_URL)
    db = _client[settings.MONGO_DB]


async def close_db():
    global db, _client
    if _client:
        _client.close()
    db = None
    _client = None
