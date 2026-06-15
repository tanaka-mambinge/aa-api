from uuid import uuid4

from pymongo import ReturnDocument

from backend.utils import utc_now


class MongoApprovalRepository:
    def __init__(self, db):
        self.collection = db.approval_requests

    async def create(
        self,
        *,
        workspace_id: str,
        requester_id: str,
        action: str,
        risk: str,
        title: str,
        summary: str,
        extra: dict[str, object],
        expires_at,
        cli_token_id: str | None = None,
    ) -> dict:
        now = utc_now()
        approval = {
            "_id": str(uuid4()),
            "workspace_id": workspace_id,
            "requester_id": requester_id,
            "action": action,
            "risk": risk,
            "status": "pending",
            "title": title,
            "summary": summary,
            "extra": extra,
            "decision": None,
            "expires_at": expires_at,
            "cli_token_id": cli_token_id,
            "created_at": now,
            "updated_at": now,
        }
        await self.collection.insert_one(approval)
        return approval

    async def list_for_requester(self, requester_id: str) -> list[dict]:
        cursor = self.collection.find({"requester_id": requester_id}).sort(
            "created_at", -1
        )
        return await cursor.to_list(length=None)

    async def get_by_id(self, approval_id: str) -> dict | None:
        return await self.collection.find_one({"_id": approval_id})

    async def transition(
        self,
        *,
        approval_id: str,
        requester_id: str,
        from_status: str,
        to_status: str,
        decision: dict[str, object] | None,
        updated_at,
    ) -> dict | None:
        return await self.collection.find_one_and_update(
            {"_id": approval_id, "requester_id": requester_id, "status": from_status},
            {
                "$set": {
                    "status": to_status,
                    "decision": decision,
                    "updated_at": updated_at,
                }
            },
            return_document=ReturnDocument.AFTER,
        )

    async def mark_timed_out(self, *, approval_id: str, updated_at) -> dict | None:
        return await self.collection.find_one_and_update(
            {"_id": approval_id, "status": "pending"},
            {"$set": {"status": "timed_out", "updated_at": updated_at}},
            return_document=ReturnDocument.AFTER,
        )
