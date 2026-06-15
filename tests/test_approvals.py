async def test_create_and_approve_approval_with_cli_token(client, registered_user):
    jwt_header = {"Authorization": f"Bearer {registered_user['token']}"}

    token_response = await client.post(
        "/api/v1/cli-tokens",
        headers=jwt_header,
        json={"name": "CLI token"},
    )
    cli_token = token_response.json()["token"]

    create_approval_response = await client.post(
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
    assert create_approval_response.status_code == 201
    approval = create_approval_response.json()
    assert approval["requester_id"] == registered_user["user"]["id"]

    list_response = await client.get("/api/v1/approvals", headers=jwt_header)
    assert list_response.status_code == 200
    assert len(list_response.json()["approvals"]) == 1

    approve_response = await client.post(
        f"/api/v1/approvals/{approval['id']}/approve",
        headers=jwt_header,
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"


async def test_revoked_cli_token_cannot_create_approval(client, registered_user):
    jwt_header = {"Authorization": f"Bearer {registered_user['token']}"}
    token_response = await client.post(
        "/api/v1/cli-tokens",
        headers=jwt_header,
        json={"name": "CLI token"},
    )
    token_payload = token_response.json()

    revoke_response = await client.post(
        f"/api/v1/cli-tokens/{token_payload['id']}/revoke",
        headers=jwt_header,
    )
    assert revoke_response.status_code == 200

    create_approval_response = await client.post(
        "/api/v1/approvals",
        headers={"Authorization": f"Bearer {token_payload['token']}"},
        json={
            "action": "domain.root.delete",
            "risk": "critical",
            "title": "Delete root domain",
            "summary": "Delete example.com",
            "extra": {},
        },
    )
    assert create_approval_response.status_code == 401
