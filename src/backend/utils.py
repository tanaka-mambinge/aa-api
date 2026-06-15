from datetime import datetime, timezone
import hashlib
import secrets


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def make_cli_token() -> tuple[str, str]:
    secret = secrets.token_urlsafe(32)
    token = f"aa_live_{secret}"
    return token, token[:12]
