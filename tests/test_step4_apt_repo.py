import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "lyux-server" / "lyux-server-api" / "src"


@pytest.fixture
def isolated_step4_api(tmp_path, monkeypatch):
    monkeypatch.setenv("LYUX_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LYUX_KEYS_DIR", str(tmp_path / "keys"))
    monkeypatch.setenv("LYUX_APT_REPO_DIR", str(tmp_path / "apt-repo"))

    for mod_name in ("main", "admin_routes", "release_registry", "profile_trust", "apt_repo"):
        sys.modules.pop(mod_name, None)

    sys.path.insert(0, str(API_DIR))
    spec = importlib.util.spec_from_file_location("main", str(API_DIR / "main.py"))
    main_mod = importlib.util.module_from_spec(spec)
    sys.modules["main"] = main_mod
    spec.loader.exec_module(main_mod)
    return main_mod, TestClient(main_mod.app)


def test_signed_apt_repo_serves_valid_deb_and_ed25519_release(isolated_step4_api):
    main_mod, client = isolated_step4_api

    rel = client.get("/api/v1/apt-repo/dists/trixie/Release")
    assert rel.status_code == 200
    assert "lyux" in rel.text.lower()

    sig = client.get("/api/v1/apt-repo/dists/trixie/Release.ed25519")
    assert sig.status_code == 200
    sig_data = sig.json()
    pub_keys = {k["key_id"]: k["public_key_pem"] for k in client.get("/api/v1/client/public-keys").json()["keys"]}
    assert main_mod.RELEASE_REGISTRY.key_manager.keys_dir
    from profile_trust import verify_ed25519_signature
    assert verify_ed25519_signature({"release": rel.text}, sig_data["signature"], pub_keys[sig_data["key_id"]]) is True

    pkgs = client.get("/api/v1/apt-repo/dists/trixie/main/binary-amd64/Packages")
    assert pkgs.status_code == 200
    assert "Package: lyux-profile-standard" in pkgs.text

    deb = client.get("/api/v1/apt-repo/pool/main/lyux-profile-standard_1.0.0_all.deb")
    assert deb.status_code == 200
    assert deb.content.startswith(b"!<arch>\n")
    assert hashlib.sha256(deb.content).hexdigest() in pkgs.text


def test_client_profile_report_and_strict_catalog_rejection(isolated_step4_api):
    main_mod, client = isolated_step4_api
    from profile_trust import validate_manifest_contract
    import datetime

    # Rapport d'application client
    rep = client.post("/api/v1/client/profile-report", json={
        "client_id": "lyux-c14-01",
        "hostname": "C14-PC01",
        "profile_id": "standard",
        "profile_version": "1.0.0",
        "state": "applied",
        "installed_packages": {"lyux-profile-standard": "1.0.0"},
    })
    assert rep.status_code == 200
    reports = client.get("/api/v1/client/profile-report").json()
    assert len(reports) == 1
    assert reports[0]["installed_packages"]["lyux-profile-standard"] == "1.0.0"

    # Rejet d'un paquet hors catalogue ou champ command libre
    km = main_mod.RELEASE_REGISTRY.key_manager
    pub = {k["key_id"]: k["public_key_pem"] for k in km.get_public_bundle()["keys"]}
    now = datetime.datetime.now(datetime.timezone.utc)
    bad_man = {
        "schema": "lyux-profile-manifest",
        "schema_version": 1,
        "profile_id": "standard",
        "profile_version": "1.0.0",
        "issued_at": (now - datetime.timedelta(minutes=1)).isoformat(),
        "expires_at": (now + datetime.timedelta(days=1)).isoformat(),
        "scope": {"building_id": "BAT-C", "room_id": "C14", "role": "eleve"},
        "artifacts": [{
            "id": "evil",
            "type": "deb",
            "package": "unapproved-hack-pkg",
            "name": "evil.deb",
            "url": "http://lyux-server:8000/api/v1/apt-repo/pool/main/evil.deb",
            "sha256": "a" * 64,
            "size": 100,
        }],
        "compatibility": {"debian": "13", "desktop": "plasma6-x11"},
    }
    bad_man["signature"], kid = km.sign_manifest(bad_man)
    ok, msg = validate_manifest_contract(bad_man, pub, key_id=kid)
    assert ok is False
    assert "catalogue" in msg.lower()
