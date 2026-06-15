from datetime import datetime
from typing import Protocol


class CliTokenRepository(Protocol):
    async def create(
        self,
        *,
        user_id: str,
        workspace_id: str,
        name: str,
        token_prefix: str,
        token_hash: str,
        expires_at: datetime | None,
    ) -> dict: ...

    async def list_for_user(self, user_id: str) -> list[dict]: ...
    async def get_by_hash(self, token_hash: str) -> dict | None: ...
    async def revoke(
        self, *, token_id: str, user_id: str, revoked_at: datetime
    ) -> dict | None: ...
    async def touch_last_used(self, token_id: str, used_at: datetime) -> None: ...
    async def get_for_user(self, token_id: str, user_id: str) -> dict | None: ...
    async def delete(self, *, token_id: str, user_id: str) -> bool: ...
