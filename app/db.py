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


async def ensure_indexes() -> None:
    await users.create_index("email", unique=True)
    await users.create_index("created_at")
    await users.create_index("role")
    await users.create_index("locked_until")

    await refresh_tokens.create_index("jti_hash", unique=True)
    await refresh_tokens.create_index("user_id")
    await refresh_tokens.create_index("expires_at")
    await refresh_tokens.create_index("revoked")

    await auth_events.create_index("ts")
    await auth_events.create_index("kind")
    await auth_events.create_index("user_id")

    await email_tokens.create_index("h", unique=True)
    await email_tokens.create_index("exp")
    await email_tokens.create_index("used")

    await reset_tokens.create_index("h", unique=True)
    await reset_tokens.create_index("exp")
    await reset_tokens.create_index("used")
