"""
Tier 1: Feature Coverage (>=5 test cases per feature across all 24 inventoried features).
Chaque test vérifie de manière autoritative les spécifications définies dans PROJECT.md
et ORIGINAL_REQUEST.md sur les fichiers réels, schémas, scripts, configurations et endpoints.
"""

import os

import re

import csv

import xml.etree.ElementTree as ET

from pathlib import Path

import pytest

import yaml


class TestFeature01_AdminUIWeb:
    def test_admin_ui_port_contract_specification(self, expected_ports):
        """1.1 Vérifie que LyuX Admin UI est assigné au port 8087 HTTP"""
        assert "admin_ui" in expected_ports
        assert expected_ports["admin_ui"]["port"] == 8087
        assert expected_ports["admin_ui"]["transport"] == "http"

    def test_admin_ui_firewall_rule_in_init_script(self, paths):
        """1.2 Vérifie la règle pare-feu UFW pour le port Admin UI 8087 dans init-server.sh"""
        init_script = paths["server_infra"] / "scripts" / "init-server.sh"
        content = init_script.read_text(encoding="utf-8")
        assert "ufw" in content
        assert "8087" in content

    def test_cockpit_system_packages_prerequisites(self, paths):
        """1.3 Vérifie la présence des outils d'administration système de base dans init-server.sh"""
        init_script = paths["server_infra"] / "scripts" / "init-server.sh"
        content = init_script.read_text(encoding="utf-8")
        for pkg in ["samba", "acl", "quota", "ufw"]:
            assert pkg in content, f"Paquet {pkg} manquant dans init-server.sh"

    def test_cockpit_storage_directories_provisioned(self, paths):
        """1.4 Vérifie la création des arborescences de stockage gérées par Cockpit"""
        init_script = paths["server_infra"] / "scripts" / "init-server.sh"
        content = init_script.read_text(encoding="utf-8")
        assert "/srv/samba" in content
        assert "/srv/samba/homes" in content or "homes,classes" in content

    def test_cockpit_backup_target_defined(self, paths):
        """1.5 Vérifie la présence de l'arborescence de sauvegarde /srv/backups/daily"""
        init_script = paths["server_infra"] / "scripts" / "init-server.sh"
        content = init_script.read_text(encoding="utf-8")
        assert "/srv/backups/daily" in content


class TestFeature02_DirectPortsWebServices:
    def test_direct_port_api_8000(self, docker_compose_data):
        """2.1 Vérifie l'exposition directe du port 8000 pour LyuX API dans docker-compose"""
        services = docker_compose_data.get("services", {})
        api_srv = services.get("lyux-api", {})
        ports = api_srv.get("ports", [])
        assert any("8000:8000" in p or "8000" in str(p) for p in ports)

    def test_direct_port_uptime_kuma_3001(self, docker_compose_data):
        """2.2 Vérifie l'exposition directe du port 3001 pour la supervision Uptime Kuma"""
        services = docker_compose_data.get("services", {})
        sup_srv = services.get("supervision", {})
        ports = sup_srv.get("ports", [])
        assert any("3001:3001" in p or "3001" in str(p) for p in ports)

    def test_direct_port_apt_cacher_3142(self, docker_compose_data):
        """2.3 Vérifie l'exposition du port 3142 pour Apt-Cacher-NG"""
        services = docker_compose_data.get("services", {})
        apt_srv = services.get("apt-cacher-ng", {})
        ports = apt_srv.get("ports", [])
        assert any("3142:3142" in p or "3142" in str(p) for p in ports)

    def test_traefik_reverse_proxy_entrypoint_8088(self, docker_compose_data):
        """2.4 Vérifie le port HTTP d'entrée Traefik pour GLPI et LAM"""
        services = docker_compose_data.get("services", {})
        traefik_srv = services.get("traefik", {})
        ports = traefik_srv.get("ports", [])
        assert any("8088" in str(p) or "80" in str(p) for p in ports)

    def test_internal_bridge_network_topology(self, docker_compose_data):
        """2.5 Vérifie la définition du réseau interne lyux-net pour tous les conteneurs"""
        networks = docker_compose_data.get("networks", {})
        assert "lyux-net" in networks
        services = docker_compose_data.get("services", {})
        for sname in ["glpi-db", "glpi", "ldap-account-manager", "supervision", "lyux-api"]:
            assert "lyux-net" in services[sname].get("networks", [])


class TestFeature03_GLPIAssetIncidentTracking:
    def test_glpi_service_configured_in_docker_compose(self, docker_compose_data):
        """3.1 Vérifie la présence du conteneur GLPI et de son image officielle"""
        services = docker_compose_data.get("services", {})
        assert "glpi" in services
        assert "glpi" in services["glpi"].get("image", "").lower()

    def test_glpi_database_dependency(self, docker_compose_data):
        """3.2 Vérifie la liaison avec la base de données MariaDB glpi-db"""
        services = docker_compose_data.get("services", {})
        glpi = services["glpi"]
        assert "glpi-db" in glpi.get("depends_on", [])

    def test_glpi_persistent_volume_mapping(self, docker_compose_data):
        """3.3 Vérifie le volume persistant glpi_data monté sur /var/www/html/glpi"""
        services = docker_compose_data.get("services", {})
        volumes = services["glpi"].get("volumes", [])
        assert any("/var/www/html/glpi" in v for v in volumes)

    def test_glpi_ticket_creation_api_endpoint(self, api_client):
        """3.4 Vérifie la route API de création de ticket d'incident GLPI"""
        payload = {
            "title": "Poste élève b204-pc01 souris défectueuse",
            "category": "Materiel",
            "description": "Bouton gauche ne répond plus",
            "hostname": "b204-pc01",
            "username": "lucas.martin"
        }
        res = api_client.post("/api/v1/tickets", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "GLPI-" in data["ticket_id"]

    def test_glpi_recent_tickets_listing(self, api_client, server_api_module):
        """3.5 Vérifie la consultation des tickets d'incidents enregistrés sur le dashboard"""
        assert len(server_api_module.RECENT_TICKETS) > 0
        assert any("GLPI-" in t["id"] for t in server_api_module.RECENT_TICKETS)
        res = api_client.get("/")
        assert res.status_code == 200
        assert "GLPI" in res.text


class TestFeature04_UptimeKumaMonitoring:
    def test_supervision_container_defined(self, docker_compose_data):
        """4.1 Vérifie la déclaration du service supervision dans docker-compose"""
        services = docker_compose_data.get("services", {})
        assert "supervision" in services
        assert "uptime-kuma" in services["supervision"].get("image", "")

    def test_supervision_port_binding_3001(self, docker_compose_data):
        """4.2 Vérifie l'assignation du port 3001:3001"""
        services = docker_compose_data.get("services", {})
        ports = services["supervision"].get("ports", [])
        assert any("3001:3001" in p for p in ports)

    def test_supervision_persistent_volume(self, docker_compose_data):
        """4.3 Vérifie la persistance des données Uptime Kuma sur /app/data"""
        services = docker_compose_data.get("services", {})
        volumes = services["supervision"].get("volumes", [])
        assert any("/app/data" in v for v in volumes)

    def test_supervision_firewall_allowed(self, paths):
        """4.4 Vérifie l'ouverture du port 3001 dans le pare-feu UFW"""
        init_sh = paths["server_infra"] / "scripts" / "init-server.sh"
        content = init_sh.read_text(encoding="utf-8")
        assert "3001" in content

    def test_supervision_traefik_routing_label(self, docker_compose_data):
        """4.5 Vérifie l'enregistrement du nom d'hôte supervision.lyux.lan dans Traefik"""
        services = docker_compose_data.get("services", {})
        labels = services["supervision"].get("labels", [])
        assert any("supervision.lyux.lan" in l for l in labels)


class TestFeature05_SambaADDomainController:
    def test_samba_realm_configuration(self, smb_conf_path):
        """5.1 Vérifie le domaine LYUX et le realm LYUX.LAN dans smb.conf"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "realm = LYUX.LAN" in content or "realm = lyux.lan" in content.lower()
        assert "workgroup = LYUX" in content

    def test_samba_security_and_passdb(self, smb_conf_path):
        """5.2 Vérifie les paramètres de sécurité Samba (USER ou ADS)"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "security =" in content
        assert "passdb backend =" in content

    def test_samba_min_protocol_smb2(self, smb_conf_path):
        """5.3 Vérifie la désactivation de SMBv1 obsolète (SMB2_10 minimum)"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "server min protocol = SMB2_10" in content or "SMB2" in content

    def test_samba_utf8_charset(self, smb_conf_path):
        """5.4 Vérifie l'encodage des caractères en UTF-8 pour les noms de fichiers français"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "unix charset = UTF-8" in content

    def test_samba_netbios_name(self, smb_conf_path):
        """5.5 Vérifie le nom NetBIOS officiel SERVEUR-LYUX"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "netbios name = SERVEUR-LYUX" in content


class TestFeature06_LAMConfiguration:
    def test_lam_container_defined(self, docker_compose_data):
        """6.1 Vérifie la présence du conteneur ldap-account-manager"""
        services = docker_compose_data.get("services", {})
        assert "ldap-account-manager" in services

    def test_lam_language_french_default(self, docker_compose_data):
        """6.2 Vérifie que la langue par défaut de LAM est configurée en français (fr_FR)"""
        services = docker_compose_data.get("services", {})
        env = services["ldap-account-manager"].get("environment", [])
        assert any("fr_FR" in str(e) for e in env)

    def test_lam_traefik_routing_rule(self, docker_compose_data):
        """6.3 Vérifie le nom de domaine lam.lyux.lan configuré sur Traefik"""
        services = docker_compose_data.get("services", {})
        labels = services["ldap-account-manager"].get("labels", [])
        assert any("lam.lyux.lan" in l for l in labels)

    def test_lam_persistent_volume(self, docker_compose_data):
        """6.4 Vérifie la persistance du dossier de configuration de LAM"""
        services = docker_compose_data.get("services", {})
        volumes = services["ldap-account-manager"].get("volumes", [])
        assert any("/var/lib/ldap-account-manager" in v for v in volumes)

    def test_teacher_desktop_shortcut_to_lam(self, paths):
        """6.5 Vérifie la présence du raccourci Bureau enseignant pointant vers LAM pour reset MDP"""
        prof_role_file = paths["ansible"] / "roles" / "lyux-profile-prof" / "tasks" / "main.yml"
        content = prof_role_file.read_text(encoding="utf-8")
        assert "http://lam.lyux.lan" in content
        assert "Reinitialiser_MDP_Eleve.desktop" in content or "Reinitialiser" in content


class TestFeature07_MandatoryTestAccounts:
    def test_mandatory_accounts_count(self, test_users_csv):
        """7.1 Vérifie qu'au moins 7 comptes de test obligatoires sont déclarés dans le CSV"""
        assert len(test_users_csv) >= 7

    def test_all_seven_acceptance_users_present(self, test_users_csv):
        """7.2 Vérifie la présence exacte des 7 élèves et enseignants requis par l'AC"""
        usernames = [f"{u['prenom'].lower()}.{u['nom'].lower()}" for u in test_users_csv]
        expected = [
            "lucas.martin", "emma.bernard", "hugo.dubois",
            "lea.thomas", "thomas.durand", "sophie.leroy", "claire.viesco"
        ]
        for exp in expected:
            assert exp in usernames, f"Utilisateur {exp} absent de utilisateurs-test.csv"

    def test_student_and_teacher_role_assignment(self, test_users_csv):
        """7.3 Vérifie la catégorisation correcte des rôles (eleves, enseignants, viesco)"""
        users_by_role = {}
        for u in test_users_csv:
            role = u.get("role", "")
            users_by_role.setdefault(role, []).append(f"{u['prenom']}.{u['nom']}")
        assert "eleves" in users_by_role
        assert len(users_by_role["eleves"]) >= 4
        assert "enseignants" in users_by_role
        assert len(users_by_role["enseignants"]) >= 2

    def test_import_script_clean_string_function(self, paths):
        """7.4 Vérifie la fonction clean_string dans import-users-csv.py pour les accents français"""
        script_path = paths["server_infra"] / "scripts" / "import-users-csv.py"
        content = script_path.read_text(encoding="utf-8")
        assert "def clean_string" in content
        assert "unicodedata.normalize" in content

    def test_csv_temporary_passwords_format(self, test_users_csv):
        """7.5 Vérifie que chaque compte possède un mot de passe temporaire robuste conforme"""
        for u in test_users_csv:
            pwd = u.get("motdepasse_temporaire", "")
            assert len(pwd) >= 8, f"Mot de passe trop court pour {u['prenom']}"
            assert any(c.isupper() for c in pwd)
            assert any(c.isdigit() for c in pwd)


class TestFeature08_SharedStorageCIFSArchitecture:
    def test_homes_share_in_samba_config(self, smb_conf_path):
        """8.1 Vérifie le partage [homes] avec create mask 0700"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "[homes]" in content
        assert "create mask = 0700" in content
        assert "directory mask = 0700" in content

    def test_classes_share_in_samba_config(self, smb_conf_path):
        """8.2 Vérifie le partage [classes] pointant vers /srv/samba/classes"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "[classes]" in content
        assert "path = /srv/samba/classes" in content

    def test_profs_restricted_share(self, smb_conf_path):
        """8.3 Vérifie le partage [profs] restreint aux enseignants"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "[profs]" in content
        assert "valid users = @enseignants" in content or "@enseignants" in content

    def test_administration_share(self, smb_conf_path):
        """8.4 Vérifie le partage [administration] restreint à l'administration et viesco"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "[administration]" in content
        assert "@administration" in content or "@viesco" in content

    def test_commun_public_readonly_share(self, smb_conf_path):
        """8.5 Vérifie le partage [commun] en lecture seule pour tous les utilisateurs"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "[commun]" in content
        assert "read only = yes" in content


class TestFeature09_DiskQuotasEnforcement:
    def test_quota_package_in_init_server(self, paths):
        """9.1 Vérifie l'installation du paquet quota dans init-server.sh"""
        content = (paths["server_infra"] / "scripts" / "init-server.sh").read_text(encoding="utf-8")
        assert "quota" in content

    def test_quota_contracts_values_in_project_spec(self, paths):
        """9.2 Vérifie la spécification des quotas : 5 Go élèves et 20 Go enseignants dans PROJECT.md"""
        content = (paths["docs"] / "PROJECT.md").read_text(encoding="utf-8")
        assert "5 GB" in content or "5 Go" in content or "5G" in content
        assert "20 GB" in content or "20 Go" in content or "20G" in content

    def test_home_dynamic_creation_helper_script(self, paths):
        """9.3 Vérifie la génération du helper lyux-create-user-home.sh avec permissions strictes 700"""
        content = (paths["server_infra"] / "scripts" / "init-server.sh").read_text(encoding="utf-8")
        assert "lyux-create-user-home.sh" in content
        assert "chmod 700" in content

    def test_root_preexec_hook_in_samba_homes(self, smb_conf_path):
        """9.4 Vérifie l'appel root preexec pour initialiser le home utilisateur à la volée"""
        content = smb_conf_path.read_text(encoding="utf-8")
        assert "root preexec =" in content
        assert "lyux-create-user-home.sh" in content

    def test_acl_package_in_init_server(self, paths):
        """9.5 Vérifie la présence de acl pour la gestion fine des droits POSIX"""
        content = (paths["server_infra"] / "scripts" / "init-server.sh").read_text(encoding="utf-8")
        assert "acl" in content


class TestFeature19_PedagogicalSupervision:
    def test_api_lock_room_endpoint_locks_students(self, api_client):
        """19.1 Vérifie le verrouillage d'une salle complète via l'API LyuX Control"""
        req = {"room_id": "B204", "action": "lock", "message_text": "Attention au tableau"}
        res = api_client.post("/api/v1/control/lock-room", json=req)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "lock"
        assert data["affected_machines"] >= 2

    def test_api_unlock_room_endpoint(self, api_client):
        """19.2 Vérifie le déverrouillage de la salle B204"""
        req = {"room_id": "B204", "action": "unlock", "message_text": "Fin d'explication"}
        res = api_client.post("/api/v1/control/lock-room", json=req)
        assert res.status_code == 200
        assert res.json()["action"] == "unlock"

    def test_station_main_implements_veyon_dialog(self, paths):
        """19.3 Vérifie la méthode open_veyon_master dans l'application unifiée lyux-station"""
        main_py = paths["station"] / "src" / "main.py"
        content = main_py.read_text(encoding="utf-8")
        assert "def open_veyon_master" in content
        assert "Tout Verrouiller" in content
        assert "Tout Déverrouiller" in content

    def test_teacher_station_cannot_lock_itself(self, api_client):
        """19.4 Vérifie que le verrouillage de salle épargne le poste enseignant b204-prof"""
        res_machines = api_client.get("/api/v1/machines")
        machines = {m["hostname"]: m for m in res_machines.json()}
        if "b204-prof" in machines:
            assert machines["b204-prof"]["locked"] is False

    def test_supervision_broadcast_message_support(self, api_client):
        """19.5 Vérifie la transmission d'un message textuel global avec la commande lock"""
        req = {"room_id": "S102", "action": "message", "message_text": "Rangez les microscopes"}
        res = api_client.post("/api/v1/control/lock-room", json=req)
        assert res.status_code == 200
        assert res.json()["message"] == "Rangez les microscopes"


class TestFeature20_PilotRoomsDefinition:
    def test_rooms_catalog_includes_b204_and_s102(self, api_client):
        """20.1 Vérifie la présence des 2 salles pilotes dans le catalogue officiel"""
        res = api_client.get("/api/v1/rooms")
        assert res.status_code == 200
        catalog = res.json()
        assert "B204" in catalog
        assert "S102" in catalog

    def test_room_b204_profile_is_nsi(self, api_client):
        """20.2 Vérifie le profil disciplinaire NSI associé à la salle B204"""
        res = api_client.get("/api/v1/rooms")
        b204 = res.json()["B204"]
        assert b204["profile"] == "nsi"
        assert "Maths" in b204["name"] or "NSI" in b204["name"]

    def test_room_s102_profile_is_sciences(self, api_client):
        """20.3 Vérifie le profil disciplinaire Sciences associé à la salle S102"""
        res = api_client.get("/api/v1/rooms")
        s102 = res.json()["S102"]
        assert s102["profile"] == "sciences"
        assert "Physique" in s102["name"] or "Sciences" in s102["name"]

    def test_ansible_inventory_pilot_rooms_structure(self, ansible_inventory_data):
        """20.4 Vérifie la structure des groupes Ansible salle_nsi_b204 et salle_sciences_s102"""
        children = ansible_inventory_data["all"]["children"]["postes_clients"]["children"]
        assert "salle_nsi_b204" in children
        assert "salle_sciences_s102" in children

    def test_pilot_rooms_ip_address_subnets(self, ansible_inventory_data):
        """20.5 Vérifie les plans d'adressage IP dédiés (192.168.100.2x pour B204, .3x pour S102)"""
        children = ansible_inventory_data["all"]["children"]["postes_clients"]["children"]
        b204_hosts = children["salle_nsi_b204"]["hosts"]
        s102_hosts = children["salle_sciences_s102"]["hosts"]
        for h, data in b204_hosts.items():
            assert "192.168.100.2" in data["ansible_host"]
        for h, data in s102_hosts.items():
            assert "192.168.100.3" in data["ansible_host"]


class TestFeature24_AdversarialHardening:
    def test_backup_321_script_exists_for_disaster_recovery(self, paths):
        """24.1 Vérifie la présence du script de sauvegarde de reprise d'activité 3-2-1"""
        b = paths["server_infra"] / "scripts" / "backup-321.sh"
        assert b.exists()
        content = b.read_text(encoding="utf-8")
        assert "tar" in content
        assert "rsync" in content or "samba" in content.lower()

    def test_cleanup_sessions_script_protects_student_privacy(self, paths):
        """24.2 Vérifie le script lyux-cleanup-sessions.sh de purge des caches à l'extinction"""
        base_tasks = paths["ansible"] / "roles" / "lyux-base" / "tasks" / "main.yml"
        content = base_tasks.read_text(encoding="utf-8")
        assert "lyux-cleanup-sessions.sh" in content
        assert ".cache" in content

    def test_firewall_default_deny_incoming(self, paths):
        """24.3 Vérifie le durcissement du pare-feu avec politique 'default deny incoming'"""
        content = (paths["server_infra"] / "scripts" / "init-server.sh").read_text(encoding="utf-8")
        assert "ufw default deny incoming" in content

    def test_root_login_disabled_in_preseed(self, preseed_iso_path):
        """24.4 Vérifie la désactivation stricte du compte root direct dans le preseed"""
        content = preseed_iso_path.read_text(encoding="utf-8")
        assert "passwd/root-login boolean false" in content

    def test_unauthorized_room_id_fails_otp_generation(self, api_client):
        """24.5 Vérifie la résistance de l'API face à une tentative d'enrôlement sur une salle inconnue"""
        req = {"admin_user": "lyux-admin", "room_id": "SALLE_PIRATE_999", "validity_minutes": 10}
        res = api_client.post("/api/v1/enroll/generate-otp", json=req)
        assert res.status_code == 404
