async def test_create_list_and_revoke_cli_token(client, registered_user):
    auth_header = {"Authorization": f"Bearer {registered_user['token']}"}

    create_response = await client.post(
        "/api/v1/cli-tokens",
        headers=auth_header,
        json={"name": "My laptop", "expires_in_days": 30},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["token"].startswith("aa_live_")

    list_response = await client.get("/api/v1/cli-tokens", headers=auth_header)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    revoke_response = await client.post(
        f"/api/v1/cli-tokens/{created['id']}/revoke",
        headers=auth_header,
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["revoked_at"] is not None


async def test_delete_cli_token_revokes_then_removes(client, registered_user):
    auth_header = {"Authorization": f"Bearer {registered_user['token']}"}

    create_response = await client.post(
        "/api/v1/cli-tokens",
        headers=auth_header,
        json={"name": "Active token", "expires_in_days": 30},
    )
    assert create_response.status_code == 201
    created = create_response.json()

    delete_response = await client.delete(
        f"/api/v1/cli-tokens/{created['id']}",
        headers=auth_header,
    )
    assert delete_response.status_code == 204

    list_response = await client.get("/api/v1/cli-tokens", headers=auth_header)
    assert list_response.status_code == 200
    assert created["id"] not in [token["id"] for token in list_response.json()]


async def test_delete_already_revoked_cli_token(client, registered_user):
    auth_header = {"Authorization": f"Bearer {registered_user['token']}"}

    create_response = await client.post(
        "/api/v1/cli-tokens",
        headers=auth_header,
        json={"name": "Revoked token", "expires_in_days": 30},
    )
    assert create_response.status_code == 201
    created = create_response.json()

    revoke_response = await client.post(
        f"/api/v1/cli-tokens/{created['id']}/revoke",
        headers=auth_header,
    )
    assert revoke_response.status_code == 200

    delete_response = await client.delete(
        f"/api/v1/cli-tokens/{created['id']}",
        headers=auth_header,
    )
    assert delete_response.status_code == 204

    list_response = await client.get("/api/v1/cli-tokens", headers=auth_header)
    assert created["id"] not in [token["id"] for token in list_response.json()]


async def test_delete_unknown_cli_token_returns_404(client, registered_user):
    auth_header = {"Authorization": f"Bearer {registered_user['token']}"}

    delete_response = await client.delete(
        "/api/v1/cli-tokens/does-not-exist",
        headers=auth_header,
    )
    assert delete_response.status_code == 404
