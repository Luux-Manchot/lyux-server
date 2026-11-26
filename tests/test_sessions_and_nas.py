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


def test_student_single_session_enforced_and_teacher_multi_session_allowed():
    admin_tok = _login("lyux-admin", "LyuxAdmin2026!")
    headers = {"Authorization": f"Bearer {admin_tok}"}
    client.post(
        "/api/v1/users/create",
        headers=headers,
        json={"username": "l.martin", "first_name": "Lucas", "last_name": "Martin", "role": "eleve", "classe": "2NDE1"},
    )
    client.post(
        "/api/v1/users/create",
        headers=headers,
        json={"username": "p.curie", "first_name": "Pierre", "last_name": "Curie", "role": "enseignant", "classe": "T-NSI"},
    )

    # Élève : première session sur PC-C14-01 autorisée
    r1 = client.post(
        "/api/v1/sessions/login-check",
        json={"username": "l.martin", "hostname": "PC-C14-01", "ip": "192.168.10.21"},
    )
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert d1["allowed"] is True
    assert d1["multi_session_allowed"] is False
    assert d1["nas"]["home_path"] == "/srv/samba/homes/l.martin"

    # Élève : deuxième session simultanée sur PC-B204-02 refusée (409)
    r2 = client.post(
        "/api/v1/sessions/login-check",
        json={"username": "l.martin", "hostname": "PC-B204-02", "ip": "192.168.10.22"},
    )
    assert r2.status_code == 409
    assert "Utilisateur déjà connecté sur le poste PC-C14-01" in r2.json()["detail"]

    # Déconnexion sur PC-C14-01 -> connexion sur PC-B204-02 autorisée avec needs_delta_sync=True
    out = client.post(
        "/api/v1/sessions/logout",
        json={"username": "l.martin", "hostname": "PC-C14-01", "files_synced": 3},
    )
    assert out.status_code == 200
    assert out.json()["last_machine"] == "PC-C14-01"

    r3 = client.post(
        "/api/v1/sessions/login-check",
        json={"username": "l.martin", "hostname": "PC-B204-02", "ip": "192.168.10.22"},
    )
    assert r3.status_code == 200
    assert r3.json()["needs_delta_sync"] is True
    assert r3.json()["last_machine"] == "PC-C14-01"

    # Nettoyage session
    client.post("/api/v1/sessions/logout", json={"username": "l.martin", "hostname": "PC-B204-02", "files_synced": 0})

    # Professeur : multi-session autorisée par défaut
    p1 = client.post("/api/v1/sessions/login-check", json={"username": "p.curie", "hostname": "PC-C14-00"})
    p2 = client.post("/api/v1/sessions/login-check", json={"username": "p.curie", "hostname": "PC-B204-00"})
    assert p1.status_code == 200 and p2.status_code == 200
    assert p2.json()["multi_session_allowed"] is True
    client.post("/api/v1/sessions/logout", json={"username": "p.curie", "hostname": "PC-C14-00"})
    client.post("/api/v1/sessions/logout", json={"username": "p.curie", "hostname": "PC-B204-00"})


def test_nas_home_path_unchanged_across_class_change_or_redoublement():
    admin_tok = _login("lyux-admin", "LyuxAdmin2026!")
    # Simulation d'un redoublement / changement de classe de l.martin
    client.put(
        "/api/v1/users/l.martin",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"classe": "1G2"},
    )
    res = client.post("/api/v1/sessions/login-check", json={"username": "l.martin", "hostname": "PC-1G2-01"})
    assert res.status_code == 200
    assert res.json()["nas"]["home_path"] == "/srv/samba/homes/l.martin"
    client.post("/api/v1/sessions/logout", json={"username": "l.martin", "hostname": "PC-1G2-01"})


def test_nss_users_and_desktop_login_flow():
    admin_tok = _login("lyux-admin", "LyuxAdmin2026!")
    # Créer un utilisateur avec mot de passe personnalisé
    create_res = client.post(
        "/api/v1/users/create",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "username": "camille.dupont",
            "first_name": "Camille",
            "last_name": "Dupont",
            "role": "eleve",
            "classe": "2GT1",
            "password": "TestPassword2026!",
        },
    )
    assert create_res.status_code in (200, 201), create_res.text

    nss_res = client.get("/api/v1/client/nss-users")
    assert nss_res.status_code == 200
    users = nss_res.json()["users"]
    entry = next((u for u in users if u["username"] == "camille.dupont"), None)
    assert entry is not None
    assert 10000 <= entry["uid"] < 60000
    assert entry["home"] == "/home/camille.dupont"

    bad_res = client.post(
        "/api/v1/auth/desktop-login",
        json={"username": "camille.dupont", "password": "wrong", "hostname": "PC-01", "ip": "192.168.10.20"},
    )
    assert bad_res.status_code == 401

    ok_res = client.post(
        "/api/v1/auth/desktop-login",
        json={"username": "camille.dupont", "password": "TestPassword2026!", "hostname": "PC-01", "ip": "192.168.10.20"},
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["authenticated"] is True
    assert ok_res.json()["uid"] == entry["uid"]

    # Ouverture de session PAM sur PC-01
    open_res = client.post(
        "/api/v1/sessions/login-check",
        json={"username": "camille.dupont", "hostname": "PC-01", "ip": "192.168.10.20"},
    )
    assert open_res.status_code == 200

    # Élève mono-session : refusé sur un second PC tant qu'il est connecté sur PC-01
    dup_res = client.post(
        "/api/v1/auth/desktop-login",
        json={"username": "camille.dupont", "password": "TestPassword2026!", "hostname": "PC-02", "ip": "192.168.10.21"},
    )
    assert dup_res.status_code == 409

    client.post("/api/v1/sessions/logout", json={"username": "camille.dupont", "hostname": "PC-01"})
