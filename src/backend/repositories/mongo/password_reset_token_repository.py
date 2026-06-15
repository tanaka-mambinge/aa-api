from uuid import uuid4

from backend.utils import utc_now


class MongoPasswordResetTokenRepository:
    def __init__(self, db):
        self.collection = db.password_reset_tokens

    async def create(self, *, user_id: str, token_hash: str, expires_at) -> dict:
        now = utc_now()
        record = {
            "_id": str(uuid4()),
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "created_at": now,
        }
        await self.collection.insert_one(record)
        return record

    async def get_by_token_hash(self, token_hash: str) -> dict | None:
        return await self.collection.find_one({"token_hash": token_hash})

    async def delete_by_user_id(self, *, user_id: str) -> None:
        await self.collection.delete_many({"user_id": user_id})

    async def delete_by_token_hash(self, token_hash: str) -> None:
        await self.collection.delete_one({"token_hash": token_hash})
