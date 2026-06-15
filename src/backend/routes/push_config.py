from fastapi import APIRouter

from backend.config import get_settings
from backend.models.push import PushConfigResponse


router = APIRouter(tags=["push-config"])


@router.get("/push-config", response_model=PushConfigResponse)
async def get_push_config() -> PushConfigResponse:
    settings = get_settings()
    return PushConfigResponse(
        enabled=bool(
            settings.web_push_vapid_private_key
            and settings.web_push_vapid_public_key
            and settings.web_push_subject
        ),
        public_key=settings.web_push_vapid_public_key or None,
    )
