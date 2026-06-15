async def test_register_and_me(client):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Ada",
            "email": "ada@example.com",
            "password": "Password123!",
            "device_type": "cli",
        },
    )

    assert register_response.status_code == 201
    token = register_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    payload = me_response.json()
    assert payload["email"] == "ada@example.com"
    assert payload["workspace_id"]


async def test_login_returns_token(client, registered_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "ada@example.com",
            "password": "Password123!",
            "device_type": "cli",
        },
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_web_login_sets_cookie_and_uses_me_without_bearer(client):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Web User",
            "email": "web@example.com",
            "password": "Password123!",
            "device_type": "web",
        },
    )

    assert register_response.status_code == 201
    assert register_response.json()["access_token"] is None
    assert "aap_access_token=" in register_response.headers.get("set-cookie", "")

    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "web@example.com"


async def test_logout_clears_cookie(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Web User",
            "email": "logout@example.com",
            "password": "Password123!",
            "device_type": "web",
        },
    )

    logout_response = await client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200

    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 401


async def test_change_password_updates_credentials(client):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Password User",
            "email": "password@example.com",
            "password": "Password123!",
            "device_type": "cli",
        },
    )

    token = register_response.json()["access_token"]

    wrong_response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "wrong-password",
            "new_password": "NewPassword123!",
        },
    )
    assert wrong_response.status_code == 400
    assert wrong_response.json()["detail"] == "Current password is incorrect"

    change_response = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword123!",
        },
    )
    assert change_response.status_code == 204

    old_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "password@example.com",
            "password": "Password123!",
            "device_type": "cli",
        },
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "password@example.com",
            "password": "NewPassword123!",
            "device_type": "cli",
        },
    )
    assert new_login.status_code == 200


async def test_forgot_and_reset_password_flow(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Reset User",
            "email": "reset@example.com",
            "password": "Password123!",
            "device_type": "cli",
        },
    )

    forgot_response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    assert forgot_response.status_code == 204

    mail_sender = client.app.state.mail_sender
    assert mail_sender.sent_messages
    body = mail_sender.sent_messages[-1].body
    token = body.split("token=")[-1].split("\n")[0].strip()

    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "ResetPassword123!"},
    )
    assert reset_response.status_code == 204

    old_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "reset@example.com",
            "password": "Password123!",
            "device_type": "cli",
        },
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "reset@example.com",
            "password": "ResetPassword123!",
            "device_type": "cli",
        },
    )
    assert new_login.status_code == 200
