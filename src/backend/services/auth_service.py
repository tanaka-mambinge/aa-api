from datetime import timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from backend.auth.security import create_access_token, hash_password, verify_password
from backend.config import Settings
from backend.utils import utc_now


def as_aware(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class AuthService:
    @staticmethod
    async def register(
        *,
        user_repository,
        workspace_repository,
        name: str,
        email: str,
        password: str,
        settings: Settings,
    ) -> tuple[dict, str]:
        existing = await user_repository.get_by_email(email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        try:
            user = await user_repository.create(
                name=name, email=email, password_hash=hash_password(password)
            )
            workspace = await workspace_repository.create_for_user(
                user_id=user["_id"], name=f"{name}'s Workspace"
            )
            await user_repository.set_workspace_id(
                user_id=user["_id"], workspace_id=workspace["_id"]
            )
        except DuplicateKeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            ) from exc

        user["workspace_id"] = workspace["_id"]
        return user, create_access_token(user["_id"], settings)

    @staticmethod
    async def login(
        *, user_repository, email: str, password: str, settings: Settings
    ) -> tuple[dict, str]:
        user = await user_repository.get_by_email(email)
        if user is None or not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        return user, create_access_token(user["_id"], settings)

    @staticmethod
    async def change_password(
        *,
        user_repository,
        user: dict,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        await user_repository.update_password(
            user_id=user["_id"], password_hash=hash_password(new_password)
        )

    @staticmethod
    async def request_password_reset(
        *,
        user_repository,
        password_reset_token_repository,
        email_sender,
        email: str,
        settings: Settings,
    ) -> None:
        user = await user_repository.get_by_email(email)
        if user is None:
            return

        token = token_urlsafe(32)
        token_hash = sha256(token.encode("utf-8")).hexdigest()
        expires_at = utc_now() + timedelta(minutes=settings.password_reset_token_expires_minutes)

        await password_reset_token_repository.delete_by_user_id(user_id=user["_id"])
        await password_reset_token_repository.create(
            user_id=user["_id"], token_hash=token_hash, expires_at=expires_at
        )

        reset_url = f"{settings.web_app_url.rstrip('/')}/reset-password?token={token}"
        await email_sender.send_password_reset(to_email=user["email"], reset_url=reset_url)

    @staticmethod
    async def reset_password(
        *,
        user_repository,
        password_reset_token_repository,
        token: str,
        new_password: str,
    ) -> None:
        token_hash = sha256(token.encode("utf-8")).hexdigest()
        record = await password_reset_token_repository.get_by_token_hash(token_hash)
        if record is None or as_aware(record["expires_at"]) <= utc_now():
            if record is not None:
                await password_reset_token_repository.delete_by_token_hash(token_hash)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user = await user_repository.get_by_id(record["user_id"])
        if user is None:
            await password_reset_token_repository.delete_by_token_hash(token_hash)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        await user_repository.update_password(
            user_id=user["_id"], password_hash=hash_password(new_password)
        )
        await password_reset_token_repository.delete_by_token_hash(token_hash)
