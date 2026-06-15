from datetime import datetime
from typing import Protocol


class ApprovalRepository(Protocol):
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
        expires_at: datetime | None,
    ) -> dict: ...

    async def list_for_requester(self, requester_id: str) -> list[dict]: ...
    async def get_by_id(self, approval_id: str) -> dict | None: ...
    async def transition(
        self,
        *,
        approval_id: str,
        requester_id: str,
        from_status: str,
        to_status: str,
        decision: dict[str, object] | None,
        updated_at: datetime,
    ) -> dict | None: ...

    async def mark_timed_out(
        self, *, approval_id: str, updated_at: datetime
    ) -> dict | None: ...
