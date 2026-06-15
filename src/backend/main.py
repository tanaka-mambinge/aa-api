from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import build_repositories, ensure_indexes
from backend.routes import (
    approvals,
    auth,
    cli_tokens,
    health,
    push_config,
    push_subscriptions,
)
from backend.services.email_service import build_email_sender
from backend.services.push_notification_service import PushNotificationService


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client, db, repositories = await build_repositories(settings)
        app.state.mongo_client = client
        app.state.mongo_db = db
        app.state.user_repository = repositories.user_repository
        app.state.workspace_repository = repositories.workspace_repository
        app.state.cli_token_repository = repositories.cli_token_repository
        app.state.password_reset_token_repository = repositories.password_reset_token_repository
        app.state.approval_repository = repositories.approval_repository
        app.state.push_subscription_repository = repositories.push_subscription_repository
        app.state.mail_sender = build_email_sender(settings)
        app.state.push_notification_service = PushNotificationService(settings)
        await ensure_indexes(db)
        yield
        client.close()

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(cli_tokens.router, prefix=settings.api_v1_prefix)
    app.include_router(approvals.router, prefix=settings.api_v1_prefix)
    app.include_router(push_config.router, prefix=settings.api_v1_prefix)
    app.include_router(push_subscriptions.router, prefix=settings.api_v1_prefix)
    return app


app = create_app()


def main() -> None:
    uvicorn.run("backend.main:app", reload=True)
