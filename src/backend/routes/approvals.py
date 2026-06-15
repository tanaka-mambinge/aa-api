import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from backend.auth.security import get_bearer_token, get_current_user
from backend.config import get_settings
from backend.models.approval import (
    ApprovalCreateRequest,
    ApprovalListResponse,
    ApprovalResponse,
)
from backend.models.common import DecisionStatus
from backend.services.approval_service import ApprovalService
from backend.services.cli_token_service import CliTokenService


router = APIRouter(prefix="/approvals", tags=["approvals"])


def serialize_approval(record: dict) -> ApprovalResponse:
    return ApprovalResponse(
        id=record["_id"],
        workspace_id=record["workspace_id"],
        requester_id=record["requester_id"],
        action=record["action"],
        risk=record["risk"],
        status=record["status"],
        title=record["title"],
        summary=record["summary"],
        extra=record["extra"],
        decision=record.get("decision"),
        expires_at=record.get("expires_at"),
        cli_token_id=record.get("cli_token_id"),
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


async def get_requester_from_bearer(
    request: Request, bearer_token: str = Depends(get_bearer_token)
) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            bearer_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
            )
        user = await request.app.state.user_repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return {**user, "cli_token_id": None}
    except jwt.PyJWTError:
        pass
    user, token_record = await CliTokenService.validate_bearer_token(
        token_repository=request.app.state.cli_token_repository,
        user_repository=request.app.state.user_repository,
        token=bearer_token,
    )
    return {**user, "cli_token_id": token_record["_id"]}


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def create_approval(
    payload: ApprovalCreateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    requester: dict = Depends(get_requester_from_bearer),
) -> ApprovalResponse:
    approval = await ApprovalService.create(
        approval_repository=request.app.state.approval_repository,
        user=requester,
        payload=payload,
    )
    background_tasks.add_task(
        request.app.state.push_notification_service.notify_new_approval,
        push_subscription_repository=request.app.state.push_subscription_repository,
        approval=approval,
    )
    return serialize_approval(approval)


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    request: Request, current_user: dict = Depends(get_current_user)
) -> ApprovalListResponse:
    approvals = await ApprovalService.list_for_user(
        approval_repository=request.app.state.approval_repository,
        user_id=current_user["_id"],
    )
    return ApprovalListResponse(
        approvals=[serialize_approval(item) for item in approvals]
    )


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: str, request: Request, current_user: dict = Depends(get_current_user)
) -> ApprovalResponse:
    approval = await ApprovalService.get_for_user(
        approval_repository=request.app.state.approval_repository,
        approval_id=approval_id,
        user_id=current_user["_id"],
    )
    return serialize_approval(approval)


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_approval(
    approval_id: str, request: Request, current_user: dict = Depends(get_current_user)
) -> ApprovalResponse:
    approval = await ApprovalService.resolve(
        approval_repository=request.app.state.approval_repository,
        approval_id=approval_id,
        user_id=current_user["_id"],
        decision_status=DecisionStatus.APPROVED,
    )
    return serialize_approval(approval)


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
async def reject_approval(
    approval_id: str, request: Request, current_user: dict = Depends(get_current_user)
) -> ApprovalResponse:
    approval = await ApprovalService.resolve(
        approval_repository=request.app.state.approval_repository,
        approval_id=approval_id,
        user_id=current_user["_id"],
        decision_status=DecisionStatus.REJECTED,
    )
    return serialize_approval(approval)


@router.post("/{approval_id}/cancel", response_model=ApprovalResponse)
async def cancel_approval(
    approval_id: str, request: Request, current_user: dict = Depends(get_current_user)
) -> ApprovalResponse:
    approval = await ApprovalService.resolve(
        approval_repository=request.app.state.approval_repository,
        approval_id=approval_id,
        user_id=current_user["_id"],
        decision_status=DecisionStatus.CANCELLED,
    )
    return serialize_approval(approval)
