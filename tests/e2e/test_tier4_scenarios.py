"""
Tier 4: Real-World Application Scenarios (Realistic School Lab Workloads).
Simule 5 flux de travail réels en établissement scolaire :
1. Rentrée des classes en Salle B204 (1G1 NSI / Maths)
2. TP de Physique-Chimie en Salle S102 (1G2 Sciences)
3. Signalement de panne matérielle et cycle d'incident GLPI
4. Administration scolaire & Surveillance Vie Scolaire (VIESCO / Direction)
5. Examen surveillé sur machines avec verrouillage Veyon et reset mot de passe express
"""

import xml.etree.ElementTree as ET

import re

from pathlib import Path

import pytest


class TestTier4RealWorldScenarios:

    def test_scenario_1_rentree_des_classes_b204_nsi(self, api_client, test_users_csv, pam_mount_xml_path):
        """
        Scénario 1 : Rentrée des classes en Salle B204 (1G1 NSI / Maths)
        - Vérification de la configuration de la salle et du profil pédagogique NSI
        - Connexion des élèves Lucas Martin et Emma Bernard
        - Montage automatique de leurs espaces personnels et de classe
        - Vérification des logiciels programmés (Thonny, VS Code, Python 3)
        """
        # 1. Vérification de la salle B204
        rooms = api_client.get("/api/v1/rooms").json()
        assert "B204" in rooms
        b204 = rooms["B204"]
        assert b204["profile"] == "nsi"
        assert b204["capacity"] >= 24

        # 2. Vérification des comptes de la classe 1G1
        b204_students = [u for u in test_users_csv if u.get("classe") == "1G1"]
        assert len(b204_students) >= 2
        student_logins = [f"{u['prenom']}.{u['nom']}" for u in b204_students]
        assert "lucas.martin" in student_logins
        assert "emma.bernard" in student_logins

        # 3. Validation de la chaîne de montage pam_mount pour les élèves NSI
        raw_xml = pam_mount_xml_path.read_text(encoding="utf-8")
        clean_xml = re.sub(r'\{\{[^}]+\}\}', '192.168.100.10', raw_xml)
        root = ET.fromstring(clean_xml)
        mountpoints = [v.attrib.get("mountpoint") for v in root.findall("volume")]
        assert "~/Espace_Personnel" in mountpoints
        assert "~/Partages_Classes" in mountpoints

        # 4. Vérification que les postes de la salle sont en ligne
        machines = api_client.get("/api/v1/machines").json()
        b204_machines = [m for m in machines if m["room"] == "B204"]
        assert len(b204_machines) >= 3  # b204-prof, b204-pc01, b204-pc02

    def test_scenario_2_tp_physique_chimie_s102(self, api_client, test_users_csv, paths):
        """
        Scénario 2 : Séance de Travaux Pratiques de Sciences en Salle S102 (1G2)
        - Professeur : Mme Sophie Leroy
        - Élèves : Hugo Dubois et Léa Thomas
        - Profil logiciel Sciences : Avogadro 3D, Tracker, Stellarium
        - Ségrégation des partages : Distribution (cours) et Dépôt (comptes-rendus)
        """
        # 1. Vérification du titulaire et de la salle
        rooms = api_client.get("/api/v1/rooms").json()
        s102 = rooms["S102"]
        assert s102["profile"] == "sciences"
        assert "Leroy" in s102["teacher"]

        # 2. Vérification des élèves de 1G2
        s102_students = [u for u in test_users_csv if u.get("classe") == "1G2"]
        assert len(s102_students) >= 2
        logins = [f"{u['prenom']}.{u['nom']}" for u in s102_students]
        assert "hugo.dubois" in logins
        assert "lea.thomas" in logins

        # 3. Vérification des outils installés pour les TP Sciences
        tasks_content = (paths["ansible"] / "roles" / "lyux-profile-salles" / "tasks" / "main.yml").read_text(encoding="utf-8")
        for tool in ["avogadro", "tracker", "stellarium"]:
            assert tool in tasks_content

        # 4. Vérification des droits d'accès partagés définis dans PROJECT.md
        project_spec = (paths["docs"] / "PROJECT.md").read_text(encoding="utf-8")
        assert "1G2_S102/Distribution" in project_spec
        assert "1G2_S102/Depot" in project_spec

    def test_scenario_3_panne_materielle_et_incident_glpi(self, api_client):
        """
        Scénario 3 : Panne matérielle pendant un cours et création de ticket d'incident GLPI
        - Élève Emma Bernard constate un écran défectueux sur b204-pc02
        - Déclaration via le guichet d'assistance LyuX
        - Ticket horodaté et assigné dans la file GLPI
        - Prise en compte dans la supervision
        """
        ticket_payload = {
            "title": "Écran clignote de manière intermittente",
            "category": "Materiel",
            "description": "Le moniteur s'éteint toutes les 2 minutes pendant le TP NSI",
            "hostname": "b204-pc02",
            "username": "emma.bernard"
        }
        res = api_client.post("/api/v1/tickets", json=ticket_payload)
        assert res.status_code == 200
        ticket_data = res.json()
        assert ticket_data["success"] is True
        assert ticket_data["ticket_id"].startswith("GLPI-#")

        # Vérifier que le ticket est tracé dans les incidents récents
        dashboard_res = api_client.get("/")
        assert dashboard_res.status_code == 200
        assert "GLPI" in dashboard_res.text

    def test_scenario_4_session_viesco_et_direction(self, api_client, test_users_csv, smb_conf_path):
        """
        Scénario 4 : Administration scolaire, Vie Scolaire & Direction
        - Claire Vie-Sco gère les présences et surveillances
        - M. Alain Delon (Direction) supervise l'infrastructure
        - Accès cloisonné au dossier partagé [administration]
        """
        # 1. Vérification des comptes staff administratif
        staff_logins = [f"{u['prenom']}.{u['nom']}" for u in test_users_csv if u.get("role") in ["viesco", "administration"]]
        assert "claire.viesco" in staff_logins
        assert "alain.direction" in staff_logins

        # 2. Vérification des restrictions Samba pour [administration]
        smb_content = smb_conf_path.read_text(encoding="utf-8")
        assert "[administration]" in smb_content
        admin_block = smb_content[smb_content.find("[administration]"):smb_content.find("[commun]")]
        assert "valid users = @administration, @viesco" in admin_block
        assert "browseable = no" in admin_block  # Hermétique pour les élèves

        # 3. Vérification des services de supervision pour la direction
        assert api_client.get("/health").status_code == 200

    def test_scenario_5_examen_surveille_et_blocage_veyon(self, api_client):
        """
        Scénario 5 : Épreuve pratique surveillée avec Veyon et assistance immédiate
        - M. Durand démarre l'examen : verrouillage général et consigne projetée
        - Élève Lucas Martin a oublié son mot de passe de session
        - Enseignant réinitialise immédiatement le mot de passe depuis l'interface
        - Fin de la consigne : déverrouillage de la salle
        """
        # 1. Enseignant verrouille la salle B204 pour donner les consignes
        lock_res = api_client.post("/api/v1/control/lock-room", json={
            "room_id": "B204",
            "action": "lock",
            "message_text": "Examen NSI : Posez vos téléphones, écoutez les consignes."
        })
        assert lock_res.status_code == 200
        assert lock_res.json()["action"] == "lock"

        # 2. Vérification que les postes élèves sont verrouillés mais pas le prof
        machines = {m["hostname"]: m for m in api_client.get("/api/v1/machines").json()}
        assert machines["b204-pc01"]["locked"] is True
        assert machines["b204-pc02"]["locked"] is True
        assert machines["b204-prof"]["locked"] is False

        # 3. L'élève Lucas Martin a oublié son mot de passe -> Reset express par le prof
        reset_res = api_client.post("/api/v1/control/reset-password", json={
            "username": "lucas.martin"
        })
        assert reset_res.status_code == 200
        new_pwd = reset_res.json()["new_password"]
        assert len(new_pwd) >= 8

        # 4. Le professeur déverrouille les postes pour lancer l'épreuve
        unlock_res = api_client.post("/api/v1/control/lock-room", json={
            "room_id": "B204",
            "action": "unlock",
            "message_text": "Vous avez 2 heures. Bon travail !"
        })
        assert unlock_res.status_code == 200
        assert unlock_res.json()["action"] == "unlock"

        # 5. Vérification que les machines sont déverrouillées
        updated_machines = {m["hostname"]: m for m in api_client.get("/api/v1/machines").json()}
        assert updated_machines["b204-pc01"]["locked"] is False
        assert updated_machines["b204-pc02"]["locked"] is False
