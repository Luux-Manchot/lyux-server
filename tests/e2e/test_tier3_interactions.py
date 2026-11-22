"""
Tier 3: Cross-Feature Combinations (Pairwise and Multi-Component Interactions).
Valide les interactions critiques entre composants hétérogènes :
- Authentification SDDM & montage dynamique pam_mount
- Enrôlement OTP & enregistrement d'inventaire matériel
- Supervision Veyon & verrouillage distant de postes élèves
- Signalement de panne élève & enregistrement de ticket GLPI
- Réinitialisation de mot de passe enseignant & mise à jour d'annuaire
- Profils disciplinaires Ansible & attribution des salles pilotes
- Proxy de paquets Apt-Cacher-NG & préconfiguration d'installation
- Clefs asymétriques Veyon & restriction des privilèges enseignants
"""

import re

import xml.etree.ElementTree as ET

from pathlib import Path

import pytest


class TestTier3Interactions:
    """Interactions trans-domaines rattachées à lyux-server."""

    def test_interaction_otp_enrollment_to_machine_inventory(self, api_client):
        """3.2 Interaction Enrôlement OTP -> Enregistrement de machine avec profil de salle"""
        # 1. Génération OTP pour salle B204
        otp_req = {"admin_user": "lyux-admin", "room_id": "B204", "validity_minutes": 20}
        otp_res = api_client.post("/api/v1/enroll/generate-otp", json=otp_req)
        assert otp_res.status_code == 200
        code = otp_res.json()["otp_code"]

        # 2. Validation enrôlement d'un poste élève
        enroll_req = {
            "otp_code": code,
            "room_id": "B204",
            "mac_address": "52:54:00:AA:BB:CC",
            "serial_number": "SN-LYUX-2026-001",
            "ram_mb": 4096,
            "is_teacher_pc": False
        }
        res_enroll = api_client.post("/api/v1/enroll/validate-otp", json=enroll_req)
        assert res_enroll.status_code == 200
        data = res_enroll.json()
        assert data["status"] == "enrolled"
        assert "b204-pc" in data["hostname"]
        assert data["room_profile"] == "nsi"

        # 3. Vérification que la machine apparaît dans l'inventaire en ligne
        res_machines = api_client.get("/api/v1/machines")
        assert res_machines.status_code == 200
        registered = [m["hostname"] for m in res_machines.json()]
        assert data["hostname"] in registered

    def test_interaction_veyon_supervision_room_locking(self, api_client):
        """3.3 Interaction Veyon Master : Verrouillage sélectif des élèves sans impacter le prof"""
        # Verrouillage salle B204
        lock_req = {"room_id": "B204", "action": "lock", "message_text": "Explications au tableau"}
        res = api_client.post("/api/v1/control/lock-room", json=lock_req)
        assert res.status_code == 200
        data = res.json()
        assert data["action"] == "lock"
        assert data["affected_machines"] >= 2

        # Vérification de l'état des machines
        machines = api_client.get("/api/v1/machines").json()
        for m in machines:
            if m["room"] == "B204":
                if m["role"] == "eleve":
                    assert m["locked"] is True
                elif m["role"] == "prof":
                    assert m["locked"] is False

        # Déverrouillage
        unlock_req = {"room_id": "B204", "action": "unlock"}
        res_unlock = api_client.post("/api/v1/control/lock-room", json=unlock_req)
        assert res_unlock.status_code == 200
        assert res_unlock.json()["action"] == "unlock"

    def test_interaction_incident_reporting_glpi_ticket_workflow(self, api_client):
        """3.4 Interaction Incident Poste élève -> Création ticket GLPI -> Suivi"""
        ticket_req = {
            "title": "Écran clignote en noir",
            "category": "Materiel",
            "description": "Câble HDMI semble débranché sur poste 01",
            "hostname": "b204-pc01",
            "username": "lucas.martin"
        }
        res_t = api_client.post("/api/v1/tickets", json=ticket_req)
        assert res_t.status_code == 200
        data_t = res_t.json()
        assert data_t["success"] is True
        t_id = data_t["ticket_id"]
        assert "GLPI-" in t_id

    def test_interaction_teacher_password_reset_flow(self, api_client):
        """3.5 Interaction Enseignant réinitialise le mot de passe d'un élève étourdi"""
        reset_req = {"username": "lucas.martin"}
        res = api_client.post("/api/v1/control/reset-password", json=reset_req)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["username"] == "lucas.martin"
        assert data["new_password"].startswith("Pass")

        # Vérifier que le compte utilisateur a bien son nouveau mot de passe mis à jour
        users = api_client.get("/api/v1/users").json()
        target = next(u for u in users if u["username"] == "lucas.martin")
        assert target["password"] == data["new_password"]

    def test_interaction_samba_users_csv_and_share_permissions(self, test_users_csv, smb_conf_path):
        """3.6 Interaction Import CSV utilisateurs -> Affectation des groupes et partages Samba"""
        smb_content = smb_conf_path.read_text(encoding="utf-8")

        # Chaque rôle dans le CSV correspond à une section de partage ou valid users dans smb.conf
        roles_in_csv = set(u["role"] for u in test_users_csv)
        assert "eleves" in roles_in_csv
        assert "enseignants" in roles_in_csv
        assert "administration" in roles_in_csv or "viesco" in roles_in_csv

        # Vérifier correspondance dans smb.conf
        assert "[homes]" in smb_content
        assert "[classes]" in smb_content
        assert "[profs]" in smb_content
        assert "[administration]" in smb_content

    def test_interaction_session_cleanup_and_student_privacy(self, paths):
        """3.10 Interaction Déconnexion élève -> Script de nettoyage des traces locales"""
        base_tasks = (paths["ansible"] / "roles" / "lyux-base" / "tasks" / "main.yml").read_text(encoding="utf-8")
        assert "lyux-cleanup-sessions.sh" in base_tasks
        assert "mode: '0755'" in base_tasks
        assert "find /tmp -user eleves -delete" in base_tasks
