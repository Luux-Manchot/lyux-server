import datetime
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRUST_PATH = ROOT / "lyux-server" / "lyux-server-api" / "src" / "profile_trust.py"

spec = importlib.util.spec_from_file_location("profile_trust", str(TRUST_PATH))
pt = importlib.util.module_from_spec(spec)
sys.modules["profile_trust"] = pt
spec.loader.exec_module(pt)


def _sample_manifest():
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "schema": "lyux-profile-manifest",
        "schema_version": 1,
        "profile_id": "nsi",
        "profile_version": "2026.11.1",
        "issued_at": (now - datetime.timedelta(minutes=5)).isoformat(timespec="seconds"),
        "expires_at": (now + datetime.timedelta(days=7)).isoformat(timespec="seconds"),
        "scope": {"building_id": "BAT-C", "room_id": "C14", "role": "eleve"},
        "artifacts": [
            {
                "id": "art-1",
                "type": "config",
                "name": "nsi-profile.json",
                "url": "https://github.com/Luux-Manchot/lyux-desktop/releases/download/v1.0.0/nsi.json",
                "sha256": "a" * 64,
                "size": 512,
            }
        ],
        "compatibility": {"debian": "13", "desktop": "plasma6-x11", "lyux_client_min": "1.0.0"},
    }


def test_ed25519_sign_and_verify_valid_manifest(tmp_path):
    km = pt.Ed25519KeyManager(keys_dir=tmp_path)
    m = _sample_manifest()
    sig, kid = km.sign_manifest(m)
    m["signature"] = sig
    bundle = km.get_public_bundle()
    pub_keys = {k["key_id"]: k["public_key_pem"] for k in bundle["keys"]}

    ok, msg = pt.validate_manifest_contract(m, pub_keys, expected_scope={"building_id": "BAT-C", "room_id": "C14", "role": "eleve"}, key_id=kid)
    assert ok is True, msg


def test_negative_cases_manifest_rejected(tmp_path):
    km = pt.Ed25519KeyManager(keys_dir=tmp_path)
    other_km = pt.Ed25519KeyManager(keys_dir=tmp_path / "other")
    bundle = km.get_public_bundle()
    pub_keys = {k["key_id"]: k["public_key_pem"] for k in bundle["keys"]}

    # 1. Signature absente
    m = _sample_manifest()
    ok, _ = pt.validate_manifest_contract(m, pub_keys)
    assert ok is False

    # 2. Signature corrompue
    sig, _ = km.sign_manifest(m)
    m["signature"] = "A" * len(sig)
    ok, _ = pt.validate_manifest_contract(m, pub_keys)
    assert ok is False

    # 3. Mauvaise clé publique
    other_sig, _ = other_km.sign_manifest(_sample_manifest())
    m["signature"] = other_sig
    ok, _ = pt.validate_manifest_contract(m, pub_keys)
    assert ok is False

    # 4. Profil inconnu
    m_bad_prof = _sample_manifest()
    m_bad_prof["profile_id"] = "hacker-profile"
    m_bad_prof["signature"], _ = km.sign_manifest(m_bad_prof)
    ok, _ = pt.validate_manifest_contract(m_bad_prof, pub_keys)
    assert ok is False

    # 5. URL arbitraire
    m_bad_url = _sample_manifest()
    m_bad_url["artifacts"][0]["url"] = "http://evil.example.com/payload.sh"
    m_bad_url["signature"], _ = km.sign_manifest(m_bad_url)
    ok, _ = pt.validate_manifest_contract(m_bad_url, pub_keys)
    assert ok is False

    # 6. Manifeste expiré et futur
    now = datetime.datetime.now(datetime.timezone.utc)
    m_exp = _sample_manifest()
    m_exp["expires_at"] = (now - datetime.timedelta(minutes=1)).isoformat(timespec="seconds")
    m_exp["signature"], _ = km.sign_manifest(m_exp)
    ok, _ = pt.validate_manifest_contract(m_exp, pub_keys)
    assert ok is False

    m_fut = _sample_manifest()
    m_fut["issued_at"] = (now + datetime.timedelta(hours=1)).isoformat(timespec="seconds")
    m_fut["signature"], _ = km.sign_manifest(m_fut)
    ok, _ = pt.validate_manifest_contract(m_fut, pub_keys)
    assert ok is False

    # 7. Portée hors établissement/salle
    m_scope = _sample_manifest()
    m_scope["signature"], _ = km.sign_manifest(m_scope)
    ok, _ = pt.validate_manifest_contract(m_scope, pub_keys, expected_scope={"building_id": "BAT-B", "room_id": "B204", "role": "eleve"})
    assert ok is False


def test_key_rotation_keeps_backup_public_key(tmp_path):
    km = pt.Ed25519KeyManager(keys_dir=tmp_path)
    m_old = _sample_manifest()
    sig_old, kid_old = km.sign_manifest(m_old)
    m_old["signature"] = sig_old

    bundle = km.rotate_key()
    assert bundle["backup_key_id"] == kid_old
    assert bundle["active_key_id"] != kid_old
    pub_keys = {k["key_id"]: k["public_key_pem"] for k in bundle["keys"]}

    # L'ancienne signature reste vérifiable via la clé de secours
    ok, _ = pt.validate_manifest_contract(m_old, pub_keys, key_id=kid_old)
    assert ok is True
