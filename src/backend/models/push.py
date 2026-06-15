from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PushSubscriptionKeys(BaseModel):
    auth: str
    p256dh: str


class PushSubscriptionCreateRequest(BaseModel):
    endpoint: str
    expiration_time: int | None = Field(default=None, alias="expirationTime")
    keys: PushSubscriptionKeys

    model_config = ConfigDict(populate_by_name=True)


class PushSubscriptionResponse(BaseModel):
    id: str
    endpoint: str
    user_id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime


class PushConfigResponse(BaseModel):
    enabled: bool
    public_key: str | None = None
