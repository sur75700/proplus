from motor.motor_asyncio import AsyncIOMotorClient

from .core.config import settings

mongo_client = AsyncIOMotorClient(settings.mongo_url)

_default = mongo_client.get_default_database()
db = _default if _default is not None else mongo_client["proplus"]

users = db["users"]
refresh_tokens = db["refresh_tokens"]
auth_events = db["auth_events"]
email_tokens = db["email_tokens"]
reset_tokens = db["reset_tokens"]


async def ping_mongo() -> bool:
    await mongo_client.admin.command("ping")
    return True
