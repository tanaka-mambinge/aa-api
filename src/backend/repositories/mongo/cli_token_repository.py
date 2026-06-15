from pymongo import ReturnDocument

from backend.utils import utc_now


class MongoCliTokenRepository:
    def __init__(self, db):
        self.collection = db.cli_tokens

    async def create(
        self,
        *,
        user_id: str,
        workspace_id: str,
        name: str,
        token_prefix: str,
        token_hash: str,
        expires_at,
    ) -> dict:
        now = utc_now()
        token = {
            "_id": token_hash[:24],
            "user_id": user_id,
            "workspace_id": workspace_id,
            "name": name,
            "token_prefix": token_prefix,
            "token_hash": token_hash,
            "last_used_at": None,
            "expires_at": expires_at,
            "revoked_at": None,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.collection.insert_one(token)
        return token

    async def list_for_user(self, user_id: str) -> list[dict]:
        cursor = self.collection.find({"user_id": user_id, "deleted_at": None}).sort(
            "created_at", -1
        )
        return await cursor.to_list(length=None)

    async def get_by_hash(self, token_hash: str) -> dict | None:
        return await self.collection.find_one({"token_hash": token_hash, "deleted_at": None})

    async def revoke(self, *, token_id: str, user_id: str, revoked_at) -> dict | None:
        return await self.collection.find_one_and_update(
            {"_id": token_id, "user_id": user_id, "revoked_at": None},
            {"$set": {"revoked_at": revoked_at, "updated_at": revoked_at}},
            return_document=ReturnDocument.AFTER,
        )

    async def touch_last_used(self, token_id: str, used_at) -> None:
        await self.collection.update_one(
            {"_id": token_id},
            {"$set": {"last_used_at": used_at, "updated_at": used_at}},
        )

    async def get_for_user(self, token_id: str, user_id: str) -> dict | None:
        return await self.collection.find_one(
            {"_id": token_id, "user_id": user_id, "deleted_at": None}
        )

    async def delete(self, *, token_id: str, user_id: str) -> bool:
        now = utc_now()
        result = await self.collection.update_one(
            {"_id": token_id, "user_id": user_id, "deleted_at": None},
            {"$set": {"deleted_at": now, "updated_at": now}},
        )
        return result.modified_count > 0
