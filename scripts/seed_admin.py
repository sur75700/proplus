import asyncio, sys
from app.models import get_user_by_email, create_user
from app.db import users

ADMIN_EMAIL = sys.argv[1] if len(sys.argv) > 1 else "admin@proplus.com"
ADMIN_PASS  = sys.argv[2] if len(sys.argv) > 2 else "AdminPassword123!"

async def main():
    u = await get_user_by_email(ADMIN_EMAIL)
    if not u:
        uid = await create_user(ADMIN_EMAIL, ADMIN_PASS)
        print("Created:", ADMIN_EMAIL, "id=", uid)
    await users.update_one({"email": ADMIN_EMAIL}, {"$set": {"role": "admin", "email_verified": True}})
    print("Promoted to admin:", ADMIN_EMAIL)

if __name__ == "__main__":
    asyncio.run(main())
