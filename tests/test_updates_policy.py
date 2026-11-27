from __future__ import annotations

import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient


def _load_server_main(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LYUX_UPDATES_POLICY_PATH", str(tmp_path / "updates_policy.json"))
    monkeypatch.setenv("LYUX_APPS_STATE_PATH", str(tmp_path / "apps_state.json"))
    main_path = Path(__file__).resolve().parent.parent / "lyux-server-api" / "src" / "main.py"
    spec = importlib.util.spec_from_file_location("lyux_server_main_updates_test", main_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_updates_policy_crud_and_apt_pinning(tmp_path: Path, monkeypatch):
    mod = _load_server_main(tmp_path, monkeypatch)
    client = TestClient(mod.app)

    resp = client.get("/api/v1/updates/policy")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["policy"].keys()) >= {"debian", "kde", "lyux", "auto_enforce"}

    put_resp = client.put(
        "/api/v1/updates/policy",
        json={
            "debian": {"selected_version": "13.1"},
            "kde": {"selected_version": "6.3.4"},
            "lyux": {"selected_version": "0.6.2"},
            "auto_enforce": True,
        },
    )
    assert put_resp.status_code == 200
    body = put_resp.json()
    assert body["policy"]["debian"]["selected_version"] == "13.1"
    assert body["policy"]["kde"]["selected_version"] == "6.3.4"
    assert body["policy"]["lyux"]["selected_version"] == "0.6.2"

    prefs = body["apt_preferences"]
    assert "Package: base-files\nPin: version 13.1*\nPin-Priority: 1001" in prefs
    assert "Package: plasma-desktop\nPin: version 6.3.4*\nPin-Priority: 1001" in prefs
    assert "Package: lyux-desktop-core\nPin: version 0.6.2*\nPin-Priority: 1001" in prefs

    client_resp = client.get("/api/v1/client/updates/policy")
    assert client_resp.status_code == 200
    c_data = client_resp.json()
    assert c_data["lyux"]["deb_url"] == "/api/v1/apt-repo/pool/main/lyux-desktop-core_0.6.2_all.deb"
    assert (tmp_path / "updates_policy.json").exists()
