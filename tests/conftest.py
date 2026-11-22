import sys
import os
import csv
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
import yaml
from fastapi.testclient import TestClient

def load_dynamic_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module

def _resolve_path(rel_path: str) -> Path:
    p = ROOT_DIR / rel_path
    if p.exists():
        return p
    # fallback to legacy projects prefix if applicable
    p_leg = ROOT_DIR / "projects" / rel_path.split("/", 1)[-1]
    return p if p.exists() else p_leg

@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT_DIR

@pytest.fixture(scope="session")
def server_api_module():
    api_path = _resolve_path("lyux-server/lyux-server-api/src/main.py")
    return load_dynamic_module("e2e_server_api", api_path)

@pytest.fixture(scope="session")
def api_client(server_api_module):
    return TestClient(server_api_module.app)

@pytest.fixture(scope="session")
def docker_compose_data() -> dict:
    dc_path = _resolve_path("lyux-server/lyux-server-infra/docker-compose.yml")
    assert dc_path.exists(), f"Fichier docker-compose introuvable : {dc_path}"
    with open(dc_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="session")
def ansible_inventory_data() -> dict:
    inv_path = _resolve_path("os-builder/lyux-ansible/inventory/hosts.yml")
    assert inv_path.exists(), f"Inventaire Ansible introuvable : {inv_path}"
    with open(inv_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="session")
def test_users_csv() -> list:
    csv_path = _resolve_path("lyux-server/lyux-server-infra/configs/utilisateurs-test.csv")
    assert csv_path.exists(), f"Fichier CSV utilisateurs introuvable : {csv_path}"
    users = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return users


ROOT_DIR = Path(__file__).resolve().parents[2]

def _dir(rel: str) -> Path:
    p = ROOT_DIR / rel
    if p.exists():
        return p
    p_leg = ROOT_DIR / "projects" / rel.split("/", 1)[-1]
    return p if p.exists() else p_leg

SERVER_INFRA_DIR = _dir("lyux-server/lyux-server-infra")

ANSIBLE_DIR = _dir("os-builder/lyux-ansible")

ENROLLMENT_DIR = _dir("lyux-desktop/applications/enrollment")

LAB_VM_DIR = _dir("os-builder/lyux-lab-vm")

ISO_BUILDER_DIR = _dir("os-builder/lyux-iso-builder")

STATION_DIR = _dir("lyux-desktop/applications/station")

WELCOME_DIR = _dir("lyux-desktop/applications/welcome")

REPORT_DIR = _dir("lyux-desktop/applications/report")

SERVER_API_DIR = _dir("lyux-server/lyux-server-api")

EXPECTED_PORTS = {
    "cockpit": {"port": 9090, "protocol": "tcp", "transport": "https", "scope": "admin"},
    "api": {"port": 8000, "protocol": "tcp", "transport": "http", "scope": "all"},
    "lam": {"port": 8082, "protocol": "tcp", "transport": "http", "scope": "admin_staff"},
    "glpi": {"port": 8085, "protocol": "tcp", "transport": "http", "scope": "all"},
    "uptime_kuma": {"port": 3001, "protocol": "tcp", "transport": "http", "scope": "admin"},
    "ldap": {"port": 389, "protocol": "tcp", "transport": "ldap", "scope": "domain"},
    "ldaps": {"port": 636, "protocol": "tcp", "transport": "ldaps", "scope": "domain"},
    "kerberos": {"port": 88, "protocol": "tcp_udp", "transport": "krb5", "scope": "domain"},
    "cifs": {"port": 445, "protocol": "tcp", "transport": "smb", "scope": "domain"},
    "veyon_service": {"port": 11100, "protocol": "tcp", "transport": "veyon", "scope": "classroom"},
    "veyon_feature": {"port": 11200, "protocol": "tcp", "transport": "veyon", "scope": "classroom"},
    "veyon_demo": {"port": 11400, "protocol": "tcp", "transport": "veyon", "scope": "classroom"},
    "apt_cache": {"port": 3142, "protocol": "tcp", "transport": "http", "scope": "proxy"}
}

MANDATORY_USERS = [
    {"username": "lucas.martin", "nom": "martin", "prenom": "lucas", "role": "eleve", "classe": "1G1", "room": "B204"},
    {"username": "emma.bernard", "nom": "bernard", "prenom": "emma", "role": "eleve", "classe": "1G1", "room": "B204"},
    {"username": "hugo.dubois", "nom": "dubois", "prenom": "hugo", "role": "eleve", "classe": "1G2", "room": "S102"},
    {"username": "lea.thomas", "nom": "thomas", "prenom": "lea", "role": "eleve", "classe": "1G2", "room": "S102"},
    {"username": "thomas.durand", "nom": "durand", "prenom": "thomas", "role": "enseignant", "classe": "Profs_Maths", "room": "B204"},
    {"username": "sophie.leroy", "nom": "leroy", "prenom": "sophie", "role": "enseignant", "classe": "Profs_Sciences", "room": "S102"},
    {"username": "claire.viesco", "nom": "viesco", "prenom": "claire", "role": "viesco", "classe": "VieScolaire", "room": "VIESCO"},
    {"username": "alain.direction", "nom": "direction", "prenom": "alain", "role": "administration", "classe": "Direction", "room": "ADMIN"}
]

@pytest.fixture(scope="session")
def mandatory_users():
    return MANDATORY_USERS

@pytest.fixture(scope="session")
def expected_ports():
    return EXPECTED_PORTS

@pytest.fixture(scope="session")
def pam_mount_xml_path():
    p = ANSIBLE_DIR / "roles" / "lyux-base" / "templates" / "pam_mount.conf.xml.j2"
    assert p.exists(), f"Fichier pam_mount introuvable : {p}"
    return p

@pytest.fixture(scope="session")
def sssd_conf_path():
    p = ANSIBLE_DIR / "roles" / "lyux-base" / "templates" / "sssd.conf.j2"
    assert p.exists(), f"Fichier sssd.conf introuvable : {p}"
    return p

@pytest.fixture(scope="session")
def smb_conf_path():
    p = SERVER_INFRA_DIR / "configs" / "samba" / "smb.conf.template"
    assert p.exists(), f"Fichier smb.conf.template introuvable : {p}"
    return p

@pytest.fixture(scope="session")
def preseed_iso_path():
    p = ISO_BUILDER_DIR / "preseed" / "preseed.cfg"
    assert p.exists(), f"Fichier preseed.cfg introuvable : {p}"
    return p

@pytest.fixture(scope="session")
def preseed_vbox_path():
    p = LAB_VM_DIR / "configs" / "vbox-preseed-kde-fr.cfg"
    assert p.exists(), f"Fichier vbox preseed introuvable : {p}"
    return p

@pytest.fixture(scope="session")
def paths():
    return {
        "root": ROOT_DIR,
        "docs": ROOT_DIR / ".github" / "docs",
        "tests_dir": ROOT_DIR / "lyux-server" / "tests",
        "server_infra": SERVER_INFRA_DIR,
        "ansible": ANSIBLE_DIR,
        "enrollment": ENROLLMENT_DIR,
        "lab_vm": LAB_VM_DIR,
        "iso_builder": ISO_BUILDER_DIR,
        "station": STATION_DIR,
        "welcome": WELCOME_DIR,
        "report": REPORT_DIR,
        "server_api": SERVER_API_DIR
    }
