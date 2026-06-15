from fastapi import APIRouter, Depends, Request, Response, status

from backend.auth.security import get_current_user
from backend.config import get_settings
from backend.models.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


def apply_auth_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="aa_access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
        max_age=settings.jwt_expires_minutes * 60,
    )


def serialize_user(user: dict) -> UserResponse:
    return UserResponse(
        id=user["_id"],
        workspace_id=user["workspace_id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest, request: Request, response: Response
) -> AuthResponse:
    user, token = await AuthService.register(
        user_repository=request.app.state.user_repository,
        workspace_repository=request.app.state.workspace_repository,
        name=payload.name,
        email=str(payload.email),
        password=payload.password,
        settings=get_settings(),
    )
    if payload.device_type.value == "web":
        apply_auth_cookie(response, token)
        return AuthResponse(user=serialize_user(user))
    return AuthResponse(
        access_token=token, token_type="bearer", user=serialize_user(user)
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest, request: Request, response: Response
) -> AuthResponse:
    user, token = await AuthService.login(
        user_repository=request.app.state.user_repository,
        email=str(payload.email),
        password=payload.password,
        settings=get_settings(),
    )
    if payload.device_type.value == "web":
        apply_auth_cookie(response, token)
        return AuthResponse(user=serialize_user(user))
    return AuthResponse(
        access_token=token, token_type="bearer", user=serialize_user(user)
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(key="aa_access_token", path="/")
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return serialize_user(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    await AuthService.change_password(
        user_repository=request.app.state.user_repository,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(payload: ForgotPasswordRequest, request: Request) -> Response:
    await AuthService.request_password_reset(
        user_repository=request.app.state.user_repository,
        password_reset_token_repository=request.app.state.password_reset_token_repository,
        email_sender=request.app.state.mail_sender,
        email=str(payload.email),
        settings=get_settings(),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(payload: ResetPasswordRequest, request: Request) -> Response:
    await AuthService.reset_password(
        user_repository=request.app.state.user_repository,
        password_reset_token_repository=request.app.state.password_reset_token_repository,
        token=payload.token,
        new_password=payload.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
