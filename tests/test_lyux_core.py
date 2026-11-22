import sys

import os

import importlib.util

from pathlib import Path

import pytest

from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[2]

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    # Ajouter le dossier parent au sys.path temporairement pour les imports relatifs
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module

def _resolve(rel: str) -> Path:
    p = BASE_DIR / rel
    if p.exists():
        return p
    p_leg = BASE_DIR / "projects" / rel.split("/", 1)[-1]
    return p if p.exists() else p_leg

api_main = load_module("server_api_main", _resolve("lyux-server/lyux-server-api/src/main.py"))

role_detector = load_module("role_detector", _resolve("lyux-desktop/applications/welcome/src/role_detector.py"))

system_info = load_module("system_info", _resolve("lyux-desktop/applications/report/src/system_info.py"))

hardware = load_module("hardware", _resolve("lyux-desktop/applications/enrollment/src/hardware.py"))

client = TestClient(api_main.app)


class TestLyuXServerAPI:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "LyuX" in data["project"]

    def test_list_rooms(self):
        response = client.get("/api/v1/rooms")
        assert response.status_code == 200
        rooms = response.json()
        assert "B204" in rooms
        assert rooms["B204"]["profile"] == "nsi"

    def test_otp_generation_and_enrollment_flow(self):
        # 1. Génération OTP
        otp_req = {"admin_user": "lyux-admin", "room_id": "B204", "validity_minutes": 15}
        resp_otp = client.post("/api/v1/enroll/generate-otp", json=otp_req)
        assert resp_otp.status_code == 200
        otp_data = resp_otp.json()
        assert "otp_code" in otp_data
        otp_code = otp_data["otp_code"]

        # 2. Validation de l'enrôlement d'un poste élève
        enroll_req = {
            "otp_code": otp_code,
            "room_id": "B204",
            "mac_address": "00:11:22:33:44:55",
            "is_teacher_pc": False
        }
        resp_enroll = client.post("/api/v1/enroll/validate-otp", json=enroll_req)
        assert resp_enroll.status_code == 200
        data_enroll = resp_enroll.json()
        assert data_enroll["status"] == "enrolled"
        assert "b204-" in data_enroll["hostname"]
        assert data_enroll["room_profile"] == "nsi"

    def test_dashboard_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "LyuX Hub" in response.text

    def test_machines_and_control(self):
        # 1. Lister les machines
        resp = client.get("/api/v1/machines")
        assert resp.status_code == 200
        machines = resp.json()
        assert len(machines) >= 2

        # 2. Verrouiller la salle B204
        lock_req = {"room_id": "B204", "action": "lock", "message_text": "Attention svp"}
        resp_lock = client.post("/api/v1/control/lock-room", json=lock_req)
        assert resp_lock.status_code == 200
        assert resp_lock.json()["action"] == "lock"

        # 3. Réinitialisation de mot de passe
        reset_req = {"username": "lucas.martin"}
        resp_reset = client.post("/api/v1/control/reset-password", json=reset_req)
        assert resp_reset.status_code == 200
        assert "Pass" in resp_reset.json()["new_password"]
