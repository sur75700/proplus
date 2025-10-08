from motor.motor_asyncio import AsyncIOMotorClient
from .core.config import settings

_client = AsyncIOMotorClient(settings.mongo_url)

# get_default_database() կարող է վերադարձնել None,
# ու Database օբյեկտը truth-test չի սատարում, դրա համար չօգտագործենք "or"
_default = _client.get_default_database()
db = _default if _default is not None else _client["proplus"]

users = db["users"]
refresh_tokens = db["refresh_tokens"]
auth_events = db["auth_events"]
email_tokens = db["email_tokens"]
reset_tokens = db["reset_tokens"]
