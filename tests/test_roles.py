from app.models.role import Role
from app.models.user_role import UserRole
from tests.conftest import TestingSessionLocal


def test_platform_role_endpoints_require_platform_admin(client, user_factory):
    normal = user_factory("normal@example.com")

    denied = client.get("/api/v1/admin/roles", headers=normal["headers"])
    assert denied.status_code == 403

    with TestingSessionLocal() as session:
        role = Role(name="platform_admin", description="Platform administrator")
        session.add(role)
        session.flush()
        session.add(UserRole(user_id=normal["user"]["id"], role_id=role.id))
        session.commit()

    allowed = client.get("/api/v1/admin/roles", headers=normal["headers"])
    assert allowed.status_code == 200
    assert any(role["name"] == "platform_admin" for role in allowed.json())

    created = client.post(
        "/api/v1/admin/roles",
        headers=normal["headers"],
        json={"name": "support", "description": "Support staff"},
    )
    assert created.status_code == 201
