from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from backend.models.common import ApprovalStatus, DecisionStatus, RiskLevel


class ApprovalCreateRequest(BaseModel):
    action: str = Field(min_length=3, max_length=120)
    risk: RiskLevel
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=500)
    extra: dict[str, object] = Field(default_factory=dict)
    expires_in_seconds: int | None = Field(default=None, ge=30, le=86400)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        parts = value.split(".")
        if len(parts) < 3 or any(not part.strip() for part in parts):
            raise ValueError(
                "Action must use dot-separated naming, e.g. domain.root.delete"
            )
        return value


class ApprovalDecision(BaseModel):
    status: DecisionStatus
    resolved_at: datetime


class ApprovalResponse(BaseModel):
    id: str
    workspace_id: str
    requester_id: str
    action: str
    risk: RiskLevel
    status: ApprovalStatus
    title: str
    summary: str
    extra: dict[str, object]
    decision: ApprovalDecision | None
    expires_at: datetime | None
    cli_token_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ApprovalListResponse(BaseModel):
    approvals: list[ApprovalResponse]
