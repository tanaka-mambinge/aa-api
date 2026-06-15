from fastapi import APIRouter, Depends, Request, status

from backend.auth.security import get_current_user
from backend.models.auth import (
    CliTokenCreateRequest,
    CliTokenCreateResponse,
    CliTokenResponse,
)
from backend.services.cli_token_service import CliTokenService


router = APIRouter(prefix="/cli-tokens", tags=["cli-tokens"])


def serialize_cli_token(record: dict) -> CliTokenResponse:
    return CliTokenResponse(
        id=record["_id"],
        name=record["name"],
        token_prefix=record["token_prefix"],
        last_used_at=record.get("last_used_at"),
        expires_at=record.get("expires_at"),
        revoked_at=record.get("revoked_at"),
        created_at=record["created_at"],
    )


@router.post(
    "", response_model=CliTokenCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_cli_token(
    payload: CliTokenCreateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> CliTokenCreateResponse:
    record, raw_token = await CliTokenService.create(
        token_repository=request.app.state.cli_token_repository,
        user=current_user,
        name=payload.name,
        expires_in_days=payload.expires_in_days,
    )
    response = serialize_cli_token(record)
    return CliTokenCreateResponse(**response.model_dump(), token=raw_token)


@router.get("", response_model=list[CliTokenResponse])
async def list_cli_tokens(
    request: Request, current_user: dict = Depends(get_current_user)
) -> list[CliTokenResponse]:
    tokens = await request.app.state.cli_token_repository.list_for_user(
        current_user["_id"]
    )
    return [serialize_cli_token(token) for token in tokens]


@router.post("/{token_id}/revoke", response_model=CliTokenResponse)
async def revoke_cli_token(
    token_id: str, request: Request, current_user: dict = Depends(get_current_user)
) -> CliTokenResponse:
    token = await CliTokenService.revoke(
        token_repository=request.app.state.cli_token_repository,
        token_id=token_id,
        user_id=current_user["_id"],
    )
    return serialize_cli_token(token)


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cli_token(
    token_id: str, request: Request, current_user: dict = Depends(get_current_user)
) -> None:
    await CliTokenService.delete(
        token_repository=request.app.state.cli_token_repository,
        token_id=token_id,
        user_id=current_user["_id"],
    )
