import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

API_MAIN_PATH = Path(__file__).resolve().parents[1] / "lyux-server-api" / "src" / "main.py"
_spec = importlib.util.spec_from_file_location("lyux_server_api_main_apps_test", API_MAIN_PATH)
server_main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server_main)


def test_apps_catalog_role_authorization_and_persistence(tmp_path, monkeypatch):
    state_file = tmp_path / "apps_state.json"
    monkeypatch.setenv("LYUX_APPS_STATE_PATH", str(state_file))
    client = TestClient(server_main.app)

    res = client.post(
        "/api/v1/apps",
        json={
            "name": "Ghidra Lab",
            "package": "ghidra-lab",
            "category": "nsi",
            "allowed_roles": ["prof", "admin"],
        },
    )
    assert res.status_code == 200, res.text
    assert state_file.exists()

    eleve_res = client.get("/api/v1/apps/client", params={"role": "eleve"})
    assert eleve_res.status_code == 200
    eleve_app = next(a for a in eleve_res.json()["apps"] if a["id"] == "ghidra-lab")
    assert eleve_app["authorized"] is False

    prof_res = client.get("/api/v1/apps/client", params={"role": "prof"})
    assert prof_res.status_code == 200
    prof_data = prof_res.json()
    assert prof_data["fallback_direct"] is True
    assert isinstance(prof_data["peer_caches"], list)
    prof_app = next(a for a in prof_data["apps"] if a["id"] == "ghidra-lab")
    assert prof_app["authorized"] is True


def test_apps_store_search_endpoint():
    client = TestClient(server_main.app)
    res = client.get("/api/v1/apps/store/search", params={"q": "inkscape", "source": "all"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1
