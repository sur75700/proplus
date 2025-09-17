from motor.motor_asyncio import AsyncIOMotorClient
from settings import settings

client: AsyncIOMotorClient | None = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB]


async def close_db():
    global client
    if client:
        client.close()
