import asyncio
import sys

from app.db import users
from app.models import create_user, get_user_by_email

ADMIN_EMAIL = sys.argv[1] if len(sys.argv) > 1 else "admin@proplus.com"
ADMIN_PASS = sys.argv[2] if len(sys.argv) > 2 else "ChangeMe123!"


async def main():
    user = await get_user_by_email(ADMIN_EMAIL)

    if not user:
        await create_user(ADMIN_EMAIL, ADMIN_PASS)

    await users.update_one(
        {"email": ADMIN_EMAIL},
        {"$set": {"role": "admin", "email_verified": True}},
    )
    print("Promoted to admin:", ADMIN_EMAIL)


if __name__ == "__main__":
    asyncio.run(main())
