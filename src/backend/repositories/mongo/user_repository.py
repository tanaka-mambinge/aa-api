from uuid import uuid4

from backend.utils import utc_now


class MongoUserRepository:
    def __init__(self, db):
        self.collection = db.users

    async def create(self, *, name: str, email: str, password_hash: str) -> dict:
        now = utc_now()
        user = {
            "_id": str(uuid4()),
            "name": name,
            "email": email.lower(),
            "password_hash": password_hash,
            "workspace_id": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.collection.insert_one(user)
        return user

    async def get_by_email(self, email: str) -> dict | None:
        return await self.collection.find_one({"email": email.lower()})

    async def get_by_id(self, user_id: str) -> dict | None:
        return await self.collection.find_one({"_id": user_id})

    async def set_workspace_id(self, *, user_id: str, workspace_id: str) -> None:
        await self.collection.update_one(
            {"_id": user_id},
            {"$set": {"workspace_id": workspace_id, "updated_at": utc_now()}},
        )

    async def update_password(self, *, user_id: str, password_hash: str) -> None:
        await self.collection.update_one(
            {"_id": user_id},
            {"$set": {"password_hash": password_hash, "updated_at": utc_now()}},
        )
