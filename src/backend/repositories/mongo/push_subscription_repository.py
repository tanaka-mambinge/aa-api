from pymongo import ReturnDocument

from backend.utils import utc_now


class MongoPushSubscriptionRepository:
    def __init__(self, db):
        self.collection = db.push_subscriptions

    async def upsert(
        self,
        *,
        user_id: str,
        workspace_id: str,
        subscription: dict,
    ) -> dict:
        now = utc_now()
        endpoint = subscription["endpoint"]
        record = await self.collection.find_one_and_update(
            {"_id": endpoint},
            {
                "$set": {
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "endpoint": endpoint,
                    "subscription": subscription,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return record

    async def list_for_workspace(self, workspace_id: str) -> list[dict]:
        cursor = self.collection.find({"workspace_id": workspace_id}).sort(
            "created_at", -1
        )
        return await cursor.to_list(length=None)

    async def delete_by_endpoint(self, endpoint: str) -> None:
        await self.collection.delete_one({"_id": endpoint})
