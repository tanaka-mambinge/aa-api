from datetime import timedelta

from fastapi import HTTPException, status

from backend.models.common import ApprovalStatus, DecisionStatus
from backend.utils import utc_now


class ApprovalService:
    @staticmethod
    async def create(*, approval_repository, user: dict, payload) -> dict:
        expires_at = None
        if payload.expires_in_seconds is not None:
            expires_at = utc_now() + timedelta(seconds=payload.expires_in_seconds)
        return await approval_repository.create(
            workspace_id=user["workspace_id"],
            requester_id=user["_id"],
            action=payload.action,
            risk=payload.risk.value,
            title=payload.title,
            summary=payload.summary,
            extra=payload.extra,
            expires_at=expires_at,
            cli_token_id=user.get("cli_token_id"),
        )

    @staticmethod
    async def list_for_user(*, approval_repository, user_id: str) -> list[dict]:
        approvals = await approval_repository.list_for_requester(user_id)
        now = utc_now()
        result: list[dict] = []
        for approval in approvals:
            if (
                approval["status"] == ApprovalStatus.PENDING.value
                and approval.get("expires_at")
                and approval["expires_at"] <= now
            ):
                updated = await approval_repository.mark_timed_out(
                    approval_id=approval["_id"], updated_at=now
                )
                if updated is not None:
                    approval = updated
            result.append(approval)
        return result

    @staticmethod
    async def get_for_user(
        *, approval_repository, approval_id: str, user_id: str
    ) -> dict:
        approval = await approval_repository.get_by_id(approval_id)
        if approval is None or approval["requester_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found"
            )
        if (
            approval["status"] == ApprovalStatus.PENDING.value
            and approval.get("expires_at")
            and approval["expires_at"] <= utc_now()
        ):
            updated = await approval_repository.mark_timed_out(
                approval_id=approval_id, updated_at=utc_now()
            )
            if updated is not None:
                approval = updated
        return approval

    @staticmethod
    async def resolve(
        *,
        approval_repository,
        approval_id: str,
        user_id: str,
        decision_status: DecisionStatus,
    ) -> dict:
        now = utc_now()
        decision = {"status": decision_status.value, "resolved_at": now}
        status_map = {
            DecisionStatus.APPROVED: ApprovalStatus.APPROVED.value,
            DecisionStatus.REJECTED: ApprovalStatus.REJECTED.value,
            DecisionStatus.CANCELLED: ApprovalStatus.CANCELLED.value,
        }
        approval = await approval_repository.transition(
            approval_id=approval_id,
            requester_id=user_id,
            from_status=ApprovalStatus.PENDING.value,
            to_status=status_map[decision_status],
            decision=decision,
            updated_at=now,
        )
        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Approval is not pending or was not found",
            )
        return approval
