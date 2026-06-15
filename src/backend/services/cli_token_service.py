from datetime import timedelta

from fastapi import HTTPException, status

from backend.utils import hash_token, make_cli_token, utc_now


class CliTokenService:
    @staticmethod
    async def create(
        *, token_repository, user: dict, name: str, expires_in_days: int | None
    ) -> tuple[dict, str]:
        raw_token, prefix = make_cli_token()
        expires_at = None
        if expires_in_days is not None:
            expires_at = utc_now() + timedelta(days=expires_in_days)
        record = await token_repository.create(
            user_id=user["_id"],
            workspace_id=user["workspace_id"],
            name=name,
            token_prefix=prefix,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
        return record, raw_token

    @staticmethod
    async def validate_bearer_token(
        *, token_repository, user_repository, token: str
    ) -> tuple[dict, dict]:
        token_hash = hash_token(token)
        record = await token_repository.get_by_hash(token_hash)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid CLI token"
            )
        now = utc_now()
        if record.get("revoked_at") is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="CLI token has been revoked",
            )
        if record.get("expires_at") is not None and record["expires_at"] <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="CLI token has expired"
            )
        await token_repository.touch_last_used(record["_id"], now)
        user = await user_repository.get_by_id(record["user_id"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token owner not found"
            )
        return user, record

    @staticmethod
    async def revoke(*, token_repository, token_id: str, user_id: str) -> dict:
        revoked = await token_repository.revoke(
            token_id=token_id, user_id=user_id, revoked_at=utc_now()
        )
        if revoked is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="CLI token not found"
            )
        return revoked

    @staticmethod
    async def delete(*, token_repository, token_id: str, user_id: str) -> None:
        existing = await token_repository.get_for_user(token_id, user_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="CLI token not found"
            )
        if existing.get("revoked_at") is None:
            await token_repository.revoke(
                token_id=token_id, user_id=user_id, revoked_at=utc_now()
            )
        await token_repository.delete(token_id=token_id, user_id=user_id)
