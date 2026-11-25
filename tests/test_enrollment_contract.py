import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
API_MAIN = ROOT / "lyux-server" / "lyux-server-api" / "src" / "main.py"

spec = importlib.util.spec_from_file_location("contract_api_main", str(API_MAIN))
api_main = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(API_MAIN.parent))
spec.loader.exec_module(api_main)

client = TestClient(api_main.app)


@pytest.fixture(autouse=True)
def reset_api_state():
    orig_machines = dict(api_main.ENROLLED_MACHINES)
    orig_enabled = api_main.SYSTEM_SETTINGS.get("enrollment_enabled", True)
    api_main.SYSTEM_SETTINGS["enrollment_enabled"] = True
    yield
    api_main.ENROLLED_MACHINES.clear()
    api_main.ENROLLED_MACHINES.update(orig_machines)
    api_main.SYSTEM_SETTINGS["enrollment_enabled"] = orig_enabled


def test_health_exposes_api_version():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["api_version"] == "1"


def test_roles_endpoint_returns_server_controlled_roles():
    r = client.get("/api/v1/enroll/roles")
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()]
    assert ids == ["eleve", "prof"]


def test_client_enroll_rejects_locked_and_invalid_catalog_entries():
    api_main.SYSTEM_SETTINGS["enrollment_enabled"] = False
    r_locked = client.post("/api/v1/enroll/client-enroll", json={
        "client_id": "lyux-test-locked",
        "hostname": "C14-PC90",
        "building_id": "BAT-C",
        "room_id": "C14",
        "role": "eleve",
    })
    assert r_locked.status_code == 403

    api_main.SYSTEM_SETTINGS["enrollment_enabled"] = True
    r_bad_b = client.post("/api/v1/enroll/client-enroll", json={
        "client_id": "lyux-test-badb",
        "hostname": "C14-PC90",
        "building_id": "BAT-X",
        "room_id": "C14",
        "role": "eleve",
    })
    assert r_bad_b.status_code == 400

    r_bad_r = client.post("/api/v1/enroll/client-enroll", json={
        "client_id": "lyux-test-badr",
        "hostname": "C14-PC90",
        "building_id": "BAT-C",
        "room_id": "B204",  # appartient à BAT-B, pas BAT-C
        "role": "eleve",
    })
    assert r_bad_r.status_code == 400


def test_client_enroll_idempotence_and_status_lookup():
    payload = {
        "client_id": "lyux-stable-001",
        "hostname": "C14-PC55",
        "building_id": "BAT-C",
        "room_id": "C14",
        "mac_address": "aa:bb:cc:dd:ee:55",
        "role": "eleve",
    }
    r1 = client.post("/api/v1/enroll/client-enroll", json=payload)
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["success"] is True
    assert d1["idempotent"] is False
    assert d1["profile"]["id"] == "nsi"
    assert d1["signature"]

    r2 = client.post("/api/v1/enroll/client-enroll", json=payload)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["idempotent"] is True
    assert d2["machine"]["hostname"] == "C14-PC55"

    st = client.get("/api/v1/enroll/status/lyux-stable-001")
    assert st.status_code == 200
    assert st.json()["enrolled"] is True
    assert st.json()["signature"] == d1["signature"]
