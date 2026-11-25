import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lyux-server-api" / "src"))
import main as server_main  # noqa: E402

client = TestClient(server_main.app)


def test_auth_login_and_me():
    bad = client.post("/api/v1/auth/login", json={"username": "lyux-admin", "password": "wrong"})
    assert bad.status_code == 401

    ok = client.post("/api/v1/auth/login", json={"username": "lyux-admin", "password": "LyuxAdmin2026!"})
    assert ok.status_code == 200
    data = ok.json()
    assert "access_token" in data
    assert data["user"]["username"] == "lyux-admin"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    assert me.json()["username"] == "lyux-admin"


def test_setup_get_and_save():
    res = client.get("/api/v1/setup")
    assert res.status_code == 200
    assert "school_name" in res.json()

    save = client.post(
        "/api/v1/setup",
        json={
            "school_name": "Lycée Jean Moulin",
            "uai_code": "0690001A",
            "academy": "Lyon",
            "domain": "lyux.lan",
            "admin_email": "contact@flowcrea.fr",
            "enrollment_enabled": True,
            "auto_update": True,
            "update_window": "22:00 – 05:00",
            "apply_topology": False,
        },
    )
    assert save.status_code == 200
    assert save.json()["setup"]["configured"] is True
    assert save.json()["setup"]["school_name"] == "Lycée Jean Moulin"


def test_roles_releases_integrations_dashboard():
    tok = client.post(
        "/api/v1/auth/login",
        json={"username": "lyux-admin", "password": "LyuxAdmin2026!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {tok}"}
    assert client.get("/api/v1/roles", headers=headers).status_code == 200
    assert client.get("/api/v1/releases").status_code == 200
    assert client.get("/api/v1/integrations/status").status_code == 200
    assert client.get("/api/v1/dashboard/summary").status_code == 200
    metrics = client.get("/api/v1/system/metrics")
    assert metrics.status_code == 200
    assert "cpu_cores" in metrics.json()
    assert "disk" in metrics.json()
