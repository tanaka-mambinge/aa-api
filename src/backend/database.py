from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient

from backend.config import Settings
from backend.repositories.mongo import (
    MongoApprovalRepository,
    MongoCliTokenRepository,
    MongoPasswordResetTokenRepository,
    MongoPushSubscriptionRepository,
    MongoUserRepository,
    MongoWorkspaceRepository,
)


@dataclass
class RepositoryContainer:
    user_repository: MongoUserRepository
    workspace_repository: MongoWorkspaceRepository
    cli_token_repository: MongoCliTokenRepository
    password_reset_token_repository: MongoPasswordResetTokenRepository
    approval_repository: MongoApprovalRepository
    push_subscription_repository: MongoPushSubscriptionRepository


def build_client(settings: Settings):
    if settings.mongo_mock:
        from mongomock_motor import AsyncMongoMockClient

        return AsyncMongoMockClient()
    return AsyncIOMotorClient(settings.mongo_uri)


async def build_repositories(settings: Settings):
    client = build_client(settings)
    db = client[settings.mongo_db]
    return (
        client,
        db,
        RepositoryContainer(
            user_repository=MongoUserRepository(db),
            workspace_repository=MongoWorkspaceRepository(db),
            cli_token_repository=MongoCliTokenRepository(db),
            password_reset_token_repository=MongoPasswordResetTokenRepository(db),
            approval_repository=MongoApprovalRepository(db),
            push_subscription_repository=MongoPushSubscriptionRepository(db),
        ),
    )


async def ensure_indexes(db) -> None:
    await db.users.create_index("email", unique=True)
    await db.cli_tokens.create_index("token_hash", unique=True)
    await db.cli_tokens.create_index("user_id")
    await db.password_reset_tokens.create_index("token_hash", unique=True)
    await db.password_reset_tokens.create_index("user_id")
    await db.password_reset_tokens.create_index("expires_at")
    await db.approval_requests.create_index("requester_id")
    await db.approval_requests.create_index("workspace_id")
    await db.approval_requests.create_index("status")
    await db.approval_requests.create_index("created_at")
    await db.push_subscriptions.create_index("workspace_id")
    await db.push_subscriptions.create_index("user_id")
