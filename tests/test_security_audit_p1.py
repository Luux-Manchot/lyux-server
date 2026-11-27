import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

API_SRC = Path(__file__).resolve().parent.parent / "lyux-server-api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from main import app  # noqa: E402

client = TestClient(app)


def test_auth_sync_requires_auth_and_never_exposes_shadow():
    # Sans authentification : doit être refusé (401/403)
    unauth = client.get("/api/v1/auth/sync")
    assert unauth.status_code in (401, 403), unauth.text
    assert "shadow" not in unauth.text.lower()

    # Avec authentification admin : 200 mais jamais de champ shadow ni de hash
    login = client.post("/api/v1/auth/login", json={"username": "lyux-admin", "password": "LyuxAdmin2026!"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    auth_resp = client.get("/api/v1/auth/sync", headers={"Authorization": f"Bearer {token}"})
    assert auth_resp.status_code == 200, auth_resp.text
    body = auth_resp.json()
    assert "shadow" not in body
    assert "shadow" not in auth_resp.text.lower()


def test_no_ed25519_private_key_tracked_in_git():
    repo_root = Path(__file__).resolve().parent.parent
    res = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "*.priv.pem", "*priv*"],
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = [line.strip() for line in res.stdout.splitlines() if line.strip() and "priv" in line.lower() and line.endswith(".pem")]
    assert tracked == [], f"Clés privées encore suivies en Git : {tracked}"

    gitignore_text = (repo_root / ".gitignore").read_text(encoding="utf-8")
    assert "*.priv.pem" in gitignore_text


def test_env_example_and_compose_have_no_default_secrets():
    infra_dir = Path(__file__).resolve().parent.parent / "lyux-server-infra"
    env_example = (infra_dir / ".env.example").read_text(encoding="utf-8")
    secret_keys = (
        "LDAP_ADMIN_PASSWORD",
        "BOR_DB_PASSWORD",
        "GLPI_DB_ROOT_PASSWORD",
        "GLPI_DB_PASSWORD",
        "LAM_ADMIN_PASSWORD",
        "GLPI_USER_TOKEN",
    )
    for line in env_example.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k, v = stripped.split("=", 1)
        if k in secret_keys:
            assert v == "", f".env.example contient une valeur non vide pour {k}"

    compose_text = (infra_dir / "docker-compose.yml").read_text(encoding="utf-8")
    for var in (
        "GLPI_DB_ROOT_PASSWORD",
        "GLPI_DB_PASSWORD",
        "LAM_ADMIN_PASSWORD",
        "GLPI_USER_TOKEN",
        "BOR_DB_PASSWORD",
    ):
        assert f"${{{var}:-" not in compose_text, f"docker-compose.yml contient un fallback faible pour {var}"
        assert f"${{{var}:?" in compose_text, f"docker-compose.yml doit échouer (fail-fast :?) si {var} manque"


def test_release_registry_preserves_package_and_compose_has_https(tmp_path):
    from release_registry import ReleaseRegistry

    reg = ReleaseRegistry(data_dir=tmp_path)
    ok, rel = reg.create_draft(
        version="1.0.99",
        profile_id="standard",
        artifacts=[
            {
                "id": "lyux-profile-standard",
                "type": "deb",
                "package": "lyux-profile-standard",
                "version": "1.0.0",
                "architecture": "all",
                "name": "lyux-profile-standard_1.0.0_all.deb",
                "url": "https://lyux-server/api/v1/apt-repo/pool/main/lyux-profile-standard_1.0.0_all.deb",
                "sha256": "a" * 64,
                "size": 100,
            }
        ],
    )
    assert ok is True
    assert rel["artifacts"][0]["package"] == "lyux-profile-standard"
    assert rel["artifacts"][0]["architecture"] == "all"

    infra_dir = Path(__file__).resolve().parent.parent / "lyux-server-infra"
    compose_text = (infra_dir / "docker-compose.yml").read_text(encoding="utf-8")
    assert "tls-init:" in compose_text
    assert "websecure" in compose_text
    assert (infra_dir / "configs" / "traefik" / "tls.yml").exists()
