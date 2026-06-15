from fastapi import APIRouter, Depends, Request

from backend.auth.security import get_current_user
from backend.models.push import (
    PushSubscriptionCreateRequest,
    PushSubscriptionResponse,
)


router = APIRouter(prefix="/push-subscriptions", tags=["push-subscriptions"])


def serialize_push_subscription(record: dict) -> PushSubscriptionResponse:
    return PushSubscriptionResponse(
        id=record["_id"],
        endpoint=record["endpoint"],
        user_id=record["user_id"],
        workspace_id=record["workspace_id"],
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


@router.post("", response_model=PushSubscriptionResponse)
async def create_push_subscription(
    payload: PushSubscriptionCreateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> PushSubscriptionResponse:
    record = await request.app.state.push_subscription_repository.upsert(
        user_id=current_user["_id"],
        workspace_id=current_user["workspace_id"],
        subscription=payload.model_dump(by_alias=True),
    )
    return serialize_push_subscription(record)
