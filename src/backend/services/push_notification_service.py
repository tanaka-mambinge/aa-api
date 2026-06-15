import asyncio
import json
import logging

from pywebpush import WebPushException, webpush

from backend.config import Settings


logger = logging.getLogger(__name__)


class PushNotificationService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def is_enabled(self) -> bool:
        return bool(
            self.settings.web_push_vapid_private_key and self.settings.web_push_subject
        )

    async def notify_new_approval(self, *, push_subscription_repository, approval: dict) -> None:
        if not self.is_enabled():
            return

        subscriptions = await push_subscription_repository.list_for_workspace(
            approval["workspace_id"]
        )
        if not subscriptions:
            return

        payload = json.dumps(
            {
                "title": "New approval request",
                "body": approval["title"],
                "summary": approval["summary"],
                "approval_id": approval["_id"],
                "workspace_id": approval["workspace_id"],
                "url": "/dashboard",
            }
        )

        await asyncio.gather(
            *(
                self._send_to_subscription(
                    push_subscription_repository=push_subscription_repository,
                    subscription=subscription,
                    payload=payload,
                )
                for subscription in subscriptions
            )
        )

    async def _send_to_subscription(
        self,
        *,
        push_subscription_repository,
        subscription: dict,
        payload: str,
    ) -> None:
        try:
            await asyncio.to_thread(
                webpush,
                subscription_info=subscription["subscription"],
                data=payload,
                vapid_private_key=self.settings.web_push_vapid_private_key,
                vapid_claims={"sub": self.settings.web_push_subject},
            )
        except WebPushException as exc:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code in {404, 410}:
                await push_subscription_repository.delete_by_endpoint(subscription["_id"])
            logger.warning(
                "Push notification failed for %s: %s",
                subscription.get("endpoint"),
                exc,
            )
