from datetime import datetime
from typing import Protocol


class PasswordResetTokenRepository(Protocol):
    async def create(
        self, *, user_id: str, token_hash: str, expires_at: datetime
    ) -> dict: ...

    async def get_by_token_hash(self, token_hash: str) -> dict | None: ...

    async def delete_by_user_id(self, *, user_id: str) -> None: ...

    async def delete_by_token_hash(self, token_hash: str) -> None: ...
