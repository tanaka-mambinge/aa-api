from uuid import uuid4

from backend.utils import utc_now


class MongoWorkspaceRepository:
    def __init__(self, db):
        self.collection = db.workspaces

    async def create_for_user(self, *, user_id: str, name: str) -> dict:
        now = utc_now()
        workspace = {
            "_id": str(uuid4()),
            "owner_user_id": user_id,
            "name": name,
            "created_at": now,
            "updated_at": now,
        }
        await self.collection.insert_one(workspace)
        return workspace

    async def get_by_id(self, workspace_id: str) -> dict | None:
        return await self.collection.find_one({"_id": workspace_id})
