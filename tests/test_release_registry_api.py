import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "lyux-server" / "lyux-server-api" / "src"


@pytest.fixture
def isolated_api(tmp_path, monkeypatch):
    monkeypatch.setenv("LYUX_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LYUX_KEYS_DIR", str(tmp_path / "keys"))

    for mod_name in ("main", "admin_routes", "release_registry", "profile_trust"):
        sys.modules.pop(mod_name, None)

    sys.path.insert(0, str(API_DIR))
    spec = importlib.util.spec_from_file_location("main", str(API_DIR / "main.py"))
    main_mod = importlib.util.module_from_spec(spec)
    sys.modules["main"] = main_mod
    spec.loader.exec_module(main_mod)
    return main_mod, TestClient(main_mod.app)


def _admin_headers(client: TestClient) -> dict:
    r = client.post("/api/v1/auth/login", json={"username": "lyux-admin", "password": "LyuxAdmin2026!"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_publish_without_signature_rejected_and_signed_flow_succeeds(isolated_api):
    _, client = isolated_api
    headers = _admin_headers(client)

    # 1. Création d'un brouillon avec SHA-256 calculé côté serveur
    r_create = client.post("/api/v1/releases", headers=headers, json={
        "version": "2.0.0",
        "profile_id": "nsi",
        "channel": "stable",
        "artifacts": [{
            "name": "nsi-2.0.0.json",
            "type": "config",
            "url": "https://github.com/Luux-Manchot/lyux-desktop/releases/download/v2.0.0/nsi.json",
            "content": "{\"kiosk\":true}",
        }],
    })
    assert r_create.status_code == 200
    rel = r_create.json()["release"]
    assert rel["state"] == "draft"
    assert len(rel["artifacts"][0]["sha256"]) == 64

    # 2. Publication sans signature -> REFUSÉE (400)
    r_pub_fail = client.post(f"/api/v1/releases/{rel['id']}/publish", headers=headers)
    assert r_pub_fail.status_code == 400

    # 3. Signature Ed25519 puis publication -> OK
    r_sign = client.post(f"/api/v1/releases/{rel['id']}/sign", headers=headers)
    assert r_sign.status_code == 200
    assert r_sign.json()["release"]["state"] == "signed"

    r_pub = client.post(f"/api/v1/releases/{rel['id']}/publish", headers=headers)
    assert r_pub.status_code == 200
    assert r_pub.json()["release"]["state"] == "published"

    # 4. Révocation puis rollback vers rel-1.0.0
    r_rev = client.post(f"/api/v1/releases/{rel['id']}/revoke", headers=headers, json={"reason": "test"})
    assert r_rev.status_code == 200
    assert r_rev.json()["release"]["state"] == "revoked"

    r_rb = client.post("/api/v1/releases/rel-1.0.0/rollback", headers=headers)
    assert r_rb.status_code == 200
    assert r_rb.json()["release"]["state"] == "published"

    # 5. Journal d'audit présent
    audit = client.get("/api/v1/releases/audit").json()["audit_log"]
    actions = [a["action"] for a in audit]
    assert "create_draft" in actions
    assert "sign" in actions
    assert "publish" in actions
    assert "revoke" in actions
    assert "rollback" in actions


def test_client_profile_manifest_requires_enrolled_client_and_returns_ed25519(isolated_api):
    _, client = isolated_api

    # Poste inconnu -> 403
    r_unauth = client.get("/api/v1/client/profile-manifest", params={
        "client_id": "unknown-id",
        "hostname": "HACK-PC",
        "building_id": "BAT-C",
        "room_id": "C14",
        "role": "eleve",
    })
    assert r_unauth.status_code == 403

    # Enrôlement préalable
    r_enroll = client.post("/api/v1/enroll/client-enroll", json={
        "client_id": "lyux-c14-test",
        "hostname": "C14-PC88",
        "building_id": "BAT-C",
        "room_id": "C14",
        "role": "eleve",
    })
    assert r_enroll.status_code == 200

    # Récupération du manifeste signé + clés publiques
    keys_res = client.get("/api/v1/client/public-keys").json()
    assert "keys" in keys_res and len(keys_res["keys"]) >= 1
    for k in keys_res["keys"]:
        assert "PRIVATE" not in k["public_key_pem"]

    r_man = client.get("/api/v1/client/profile-manifest", params={
        "client_id": "lyux-c14-test",
        "hostname": "C14-PC88",
        "building_id": "BAT-C",
        "room_id": "C14",
        "role": "eleve",
        "schema_version": 1,
    })
    assert r_man.status_code == 200
    data = r_man.json()
    assert data["manifest"]["schema"] == "lyux-profile-manifest"
    assert data["detached_signature"]
    assert data["public_key_id"] == keys_res["active_key_id"]
