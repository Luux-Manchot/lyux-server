import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lyux-server-api" / "src"))
import main as server_main  # noqa: E402

client = TestClient(server_main.app)


def _login(username: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_default_roles_and_technicien_distinct_from_admin():
    tok = _login("lyux-admin", "LyuxAdmin2026!")
    res = client.get("/api/v1/roles", headers={"Authorization": f"Bearer {tok}"})
    assert res.status_code == 200
    data = res.json()
    assert data["schema"] == "lyux-rbac-matrix"
    assert data["schema_version"] == 1
    role_ids = [r["id"] for r in data["roles"]]
    for expected in ("admin", "technicien", "direction", "viesco", "enseignant", "eleve"):
        assert expected in role_ids


def test_multi_role_highest_priority_effective_role_and_cumulative_permissions():
    admin_tok = _login("lyux-admin", "LyuxAdmin2026!")
    # Création d'un compte avec deux rôles : enseignant (40) + technicien (85)
    create_res = client.post(
        "/api/v1/users/create",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "username": "j.multirole",
            "first_name": "Jean",
            "last_name": "Multirole",
            "role": "enseignant",
            "classe": "T-NSI",
        },
    )
    assert create_res.status_code == 200, create_res.text
    created_pwd = create_res.json()["user"]["password"]

    # Attribution des deux rôles via PUT /api/v1/users/{username}
    upd = client.put(
        "/api/v1/users/j.multirole",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"roles": ["enseignant", "technicien"]},
    )
    assert upd.status_code == 200, upd.text
    user_view = upd.json()["user"]
    assert user_view["effective_role"] == "technicien"
    assert set(user_view["roles"]) == {"enseignant", "technicien"}
    assert user_view["permissions"]["parc.manage"] is True
    assert user_view["permissions"]["parc.room_lock"] is True
    assert user_view["permissions"]["roles.manage"] is False

    # Vérification /auth/me avec le compte multi-rôles
    user_tok = _login("j.multirole", created_pwd)
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {user_tok}"})
    assert me.status_code == 200
    assert me.json()["effective_role"] == "technicien"
    assert me.json()["permissions"]["releases.manage"] is True
    assert me.json()["permissions"]["roles.manage"] is False

    # Un utilisateur sans roles.manage reçoit 403 sur POST /api/v1/roles
    forbidden = client.post(
        "/api/v1/roles",
        headers={"Authorization": f"Bearer {user_tok}"},
        json={"name": "Referent NSI", "priority": 45},
    )
    assert forbidden.status_code == 403


def test_custom_role_lifecycle_and_system_role_protection():
    admin_tok = _login("lyux-admin", "LyuxAdmin2026!")
    headers = {"Authorization": f"Bearer {admin_tok}"}

    # Un rôle système ne peut pas être supprimé
    del_sys = client.delete("/api/v1/roles/technicien", headers=headers)
    assert del_sys.status_code == 400

    # Création puis suppression d'un rôle personnalisé
    created = client.post(
        "/api/v1/roles",
        headers=headers,
        json={
            "id": "referent-labo",
            "name": "Référent Labo",
            "description": "Gestion des logiciels de sciences",
            "priority": 50,
            "permissions": {"dashboard.view": True, "apps.manage": True},
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["role"]["id"] == "referent-labo"

    deleted = client.delete("/api/v1/roles/referent-labo", headers=headers)
    assert deleted.status_code == 200
