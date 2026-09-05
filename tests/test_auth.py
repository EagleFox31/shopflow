import jwt

from app.core.config import settings


def test_register_login_refresh_and_profile_contract(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "Test.User@Example.com",
            "full_name": "Test User",
            "password": "strong-password",
        },
    )
    assert register.status_code == 201
    body = register.json()
    assert set(body) == {"id", "email", "full_name", "is_active", "created_at"}
    assert body["email"] == "test.user@example.com"
    assert "password" not in body
    assert "hashed_password" not in body

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test.user@example.com",
            "full_name": "Duplicate",
            "password": "strong-password",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "Email already registered"}

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "test.user@example.com", "password": "strong-password"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert set(tokens) == {"access_token", "refresh_token", "token_type"}
    assert tokens["token_type"] == "bearer"

    access_payload = jwt.decode(
        tokens["access_token"], settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    refresh_payload = jwt.decode(
        tokens["refresh_token"], settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    assert access_payload["sub"] == str(body["id"])

    me = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == body["id"]

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    assert refreshed.json()["refresh_token"]


def test_auth_rejects_invalid_credentials_and_wrong_token_type(client, user_factory):
    user = user_factory("auth@example.com")

    bad_login = client.post(
        "/api/v1/auth/login",
        data={"username": user["email"], "password": "wrong-password"},
    )
    assert bad_login.status_code == 401
    assert bad_login.json()["detail"] == "Invalid credentials"

    no_token = client.get("/api/v1/users/me")
    assert no_token.status_code == 401

    access_as_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": user["tokens"]["access_token"]},
    )
    assert access_as_refresh.status_code == 401
    assert access_as_refresh.json()["detail"] == "Invalid token type"

    refresh_as_access = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user['tokens']['refresh_token']}"},
    )
    assert refresh_as_access.status_code == 401

    malformed = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer definitely-not-a-jwt"},
    )
    assert malformed.status_code == 401


def test_password_change_invalidates_old_password(client, user_factory):
    user = user_factory("password@example.com")

    wrong_current = client.post(
        "/api/v1/users/me/change-password",
        headers=user["headers"],
        json={"current_password": "not-current", "new_password": "new-password-123"},
    )
    assert wrong_current.status_code == 401

    changed = client.post(
        "/api/v1/users/me/change-password",
        headers=user["headers"],
        json={"current_password": user["password"], "new_password": "new-password-123"},
    )
    assert changed.status_code == 200
    assert changed.json() == {"message": "Password updated"}

    old_login = client.post(
        "/api/v1/auth/login",
        data={"username": user["email"], "password": user["password"]},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        data={"username": user["email"], "password": "new-password-123"},
    )
    assert new_login.status_code == 200


def test_request_validation_contracts_return_422(client):
    invalid_user = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "full_name": "X", "password": "short"},
    )
    assert invalid_user.status_code == 422
    assert "detail" in invalid_user.json()
