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


def test_global_profiles_independent_of_room_and_layered_resolution():
    admin_tok = _login("lyux-admin", "LyuxAdmin2026!")
    headers = {"Authorization": f"Bearer {admin_tok}"}

    res = client.get("/api/v1/profiles", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["location_independent"] is True
    assert data["resolution_layers"] == ["global", "school", "role", "group", "user", "machine"]

    # Création d'un profil personnalisé global + affectation utilisateur
    up = client.post(
        "/api/v1/profiles",
        headers=headers,
        json={
            "id": "robotique",
            "name": "Club Robotique",
            "description": "Outils Arduino et Python",
            "scope": "user",
            "kiosk_locked": False,
            "packages": ["arduino", "thonny"],
        },
    )
    assert up.status_code == 200

    asg = client.post(
        "/api/v1/profiles/assign",
        headers=headers,
        json={"target_type": "user", "target_id": "m.curie", "profile_id": "robotique"},
    )
    assert asg.status_code == 200

    # Résolution pour m.curie (rôle enseignant, groupe T-NSI) sur deux postes différents
    r1 = client.get("/api/v1/profiles/resolve?username=m.curie&role=enseignant&groups=T-NSI&hostname=PC-TEST-A")
    r2 = client.get("/api/v1/profiles/resolve?username=m.curie&role=enseignant&groups=T-NSI&hostname=PC-TEST-B")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["applied_profiles"] == r2.json()["applied_profiles"]
    assert r1.json()["applied_profiles"] == ["global-socle", "enseignant", "nsi", "robotique"]
    assert "arduino" in r1.json()["packages"]
    assert r1.json()["location_independent"] is True


def test_profile_assign_rejects_room_or_building_targets():
    admin_tok = _login("lyux-admin", "LyuxAdmin2026!")
    bad = client.post(
        "/api/v1/profiles/assign",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"target_type": "room", "target_id": "C14", "profile_id": "nsi"},
    )
    assert bad.status_code == 400


def test_step5_preview_pilot_reset_and_catalog_validation():
    admin_tok = _login("lyux-admin", "LyuxAdmin2026!")
    headers = {"Authorization": f"Bearer {admin_tok}"}

    # Rejet d'un thème ou paquet hors catalogue signé
    bad_theme = client.post(
        "/api/v1/profiles",
        headers=headers,
        json={"id": "eleve", "name": "Profil Élève", "desktop_theme": "http://evil/theme", "packages": []},
    )
    assert bad_theme.status_code == 400

    bad_pkg = client.post(
        "/api/v1/profiles",
        headers=headers,
        json={"id": "eleve", "name": "Profil Élève", "desktop_theme": "lyux-ocean", "packages": ["curl-pipe-sh"]},
    )
    assert bad_pkg.status_code == 400

    # Prévisualisation avant publication
    prev = client.post(
        "/api/v1/profiles/preview",
        headers=headers,
        json={"profile_id": "eleve", "desktop_theme": "lyux-dark", "packages": ["thonny", "geogebra"], "kiosk_locked": True, "target_type": "role", "target_id": "eleve"},
    )
    assert prev.status_code == 200
    assert prev.json()["pilot_recommended"] is True

    # Application sur un poste pilote puis retour au profil par défaut
    pilot = client.post(
        "/api/v1/profiles/pilot",
        headers=headers,
        json={"profile_id": "eleve", "target_type": "machine", "target_id": "PC-C14-01"},
    )
    assert pilot.status_code == 200

    rst = client.post("/api/v1/profiles/eleve/reset", headers=headers)
    assert rst.status_code == 200
    assert rst.json()["profile"]["desktop_theme"] == "lyux-ocean"

    # Journal d'audit présent
    prof_list = client.get("/api/v1/profiles", headers=headers).json()
    assert len(prof_list["audit_log"]) >= 2

    # Retrait d'une affectation
    unassign = client.post(
        "/api/v1/profiles/unassign",
        headers=headers,
        json={"target_type": "machine", "target_id": "PC-C14-01", "profile_id": "eleve"},
    )
    assert unassign.status_code == 200
