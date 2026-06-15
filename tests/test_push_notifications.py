import json


async def test_create_push_subscription(client, registered_user):
    auth_header = {"Authorization": f"Bearer {registered_user['token']}"}

    response = await client.post(
        "/api/v1/push-subscriptions",
        headers=auth_header,
        json={
            "endpoint": "https://push.example.com/subscriptions/123",
            "expirationTime": None,
            "keys": {
                "auth": "auth-token",
                "p256dh": "public-key",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["endpoint"] == "https://push.example.com/subscriptions/123"
    assert payload["workspace_id"] == registered_user["user"]["workspace_id"]


async def test_create_approval_triggers_push_notification(client, registered_user, monkeypatch):
    auth_header = {"Authorization": f"Bearer {registered_user['token']}"}

    await client.post(
        "/api/v1/push-subscriptions",
        headers=auth_header,
        json={
            "endpoint": "https://push.example.com/subscriptions/abc",
            "expirationTime": None,
            "keys": {
                "auth": "auth-token",
                "p256dh": "public-key",
            },
        },
    )

    app = client._transport.app
    app.state.push_notification_service.settings.web_push_vapid_private_key = "test-private-key"
    app.state.push_notification_service.settings.web_push_vapid_public_key = "test-public-key"
    app.state.push_notification_service.settings.web_push_subject = "mailto:test@example.com"

    sent_messages: list[dict] = []

    def fake_webpush(*, subscription_info, data, vapid_private_key, vapid_claims):
        sent_messages.append(
            {
                "subscription_info": subscription_info,
                "data": json.loads(data),
                "vapid_private_key": vapid_private_key,
                "vapid_claims": vapid_claims,
            }
        )

    monkeypatch.setattr("backend.services.push_notification_service.webpush", fake_webpush)

    token_response = await client.post(
        "/api/v1/cli-tokens",
        headers=auth_header,
        json={"name": "CLI token"},
    )
    cli_token = token_response.json()["token"]

    create_response = await client.post(
        "/api/v1/approvals",
        headers={"Authorization": f"Bearer {cli_token}"},
        json={
            "action": "domain.root.delete",
            "risk": "critical",
            "title": "Delete root domain",
            "summary": "Delete example.com",
            "extra": {"domain": "example.com"},
        },
    )

    assert create_response.status_code == 201
    assert sent_messages
    assert sent_messages[0]["subscription_info"]["endpoint"] == "https://push.example.com/subscriptions/abc"
    assert sent_messages[0]["data"]["approval_id"] == create_response.json()["id"]
