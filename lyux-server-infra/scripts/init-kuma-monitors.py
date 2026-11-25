#!/usr/bin/env python3
"""
Opération Manchot (LyuX) — Provisioning Automatisé des Sondes Uptime Kuma
Milestone 1 : Server Stack & Cockpit Integration
Auteur : Explorer M1-3

Ce script initialise ou met à jour les sondes de supervision officielles dans
la base de données SQLite d'Uptime Kuma (kuma.db). Il est strictement idempotent.
"""

import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path

# Détection de l'environnement et du chemin de la base
DEFAULT_DB_LOCATIONS = [
    os.environ.get("KUMA_DB_PATH"),
    "/app/data/kuma.db",  # Inside Uptime Kuma container
    "data/uptime-kuma/kuma.db",  # Relative to lyux-server-infra
    "lyux-server/lyux-server-infra/data/uptime-kuma/kuma.db",
    "lyux-server-infra/data/uptime-kuma/kuma.db",
]

TARGET_HOST = os.environ.get("LYUX_HOST", "host.docker.internal")
SERVER_IP = os.environ.get("LYUX_SERVER_IP", "192.168.100.10")
DOMAIN = os.environ.get("LYUX_DOMAIN", "lyux.lan")

# Définition des sondes officielles Opération Manchot (LyuX)
OFFICIAL_MONITORS = [
    {
        "name": "LyuX Admin UI",
        "type": "http",
        "url": f"http://{TARGET_HOST}:8087",
        "hostname": None,
        "port": None,
        "interval": 60,
        "retry_interval": 10,
        "maxretries": 2,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-299"]),
        "description": "Interface unique d'administration LyuX (HTTP 8087)"
    },
    {
        "name": "LyuX Control API",
        "type": "http",
        "url": f"http://{TARGET_HOST}:8000/health",
        "hostname": None,
        "port": None,
        "interval": 30,
        "retry_interval": 5,
        "maxretries": 2,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-299"]),
        "description": "API FastAPI d'enrôlement et de contrôle central LyuX (port 8000)"
    },
    {
        "name": "LDAP Account Manager (LAM)",
        "type": "http",
        "url": f"http://{TARGET_HOST}:8082",
        "hostname": None,
        "port": None,
        "interval": 60,
        "retry_interval": 10,
        "maxretries": 2,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-399"]),
        "description": "Portail web d'administration de l'annuaire Samba-AD / LDAP (port 8082)"
    },
    {
        "name": "GLPI Helpdesk & Inventory",
        "type": "http",
        "url": f"http://{TARGET_HOST}:8085",
        "hostname": None,
        "port": None,
        "interval": 60,
        "retry_interval": 10,
        "maxretries": 2,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-399"]),
        "description": "Gestion de parc informatique et suivi des tickets d'assistance GLPI (port 8085)"
    },
    {
        "name": "Samba-AD LDAP Directory",
        "type": "port",
        "url": None,
        "hostname": TARGET_HOST,
        "port": 389,
        "interval": 30,
        "retry_interval": 5,
        "maxretries": 2,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-299"]),
        "description": "Annuaire centralisé LDAP Samba-AD pour SSSD et authentification (port TCP 389)"
    },
    {
        "name": "Samba SMB File Sharing",
        "type": "port",
        "url": None,
        "hostname": TARGET_HOST,
        "port": 445,
        "interval": 30,
        "retry_interval": 5,
        "maxretries": 2,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-299"]),
        "description": "Partages CIFS /homes et /classes pour les postes élèves et enseignants (port TCP 445)"
    },
    # Sondes complémentaires recommandées pour la robustesse du réseau scolaire
    {
        "name": "Apt-Cacher-NG Local Cache",
        "type": "http",
        "url": f"http://{TARGET_HOST}:3142",
        "hostname": None,
        "port": None,
        "interval": 60,
        "retry_interval": 10,
        "maxretries": 1,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-399"]),
        "description": "Serveur proxy/cache local de paquets Debian/Ubuntu (port 3142)"
    },
    {
        "name": "Veyon Pilot Prof B204",
        "type": "port",
        "url": None,
        "hostname": "192.168.100.20",
        "port": 11100,
        "interval": 60,
        "retry_interval": 10,
        "maxretries": 2,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-299"]),
        "description": "Poste Enseignant Salle B204 NSI (Veyon Service 11100)"
    },
    {
        "name": "Veyon Pilot Prof S102",
        "type": "port",
        "url": None,
        "hostname": "192.168.100.30",
        "port": 11100,
        "interval": 60,
        "retry_interval": 10,
        "maxretries": 2,
        "ignore_tls": 0,
        "accepted_statuscodes_json": json.dumps(["200-299"]),
        "description": "Poste Enseignant Salle S102 Sciences (Veyon Service 11100)"
    }
]


def find_db():
    for loc in DEFAULT_DB_LOCATIONS:
        if loc and os.path.exists(loc):
            return loc
    return None


def provision_monitors(db_path: str):
    print(f"[*] Connexion à la base SQLite Uptime Kuma : {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Vérification de l'existence de la table monitor
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monitor';")
    if not cursor.fetchone():
        print("[!] Erreur : La table 'monitor' n'existe pas encore dans cette base.")
        print("[!] Uptime Kuma doit démarrer au moins une fois pour générer son schéma.")
        conn.close()
        return False

    inserted = 0
    updated = 0

    for m in OFFICIAL_MONITORS:
        cursor.execute("SELECT id, type, url, hostname, port FROM monitor WHERE name = ?", (m["name"],))
        row = cursor.fetchone()

        if row:
            mon_id = row[0]
            cursor.execute("""
                UPDATE monitor SET
                    type = ?,
                    url = ?,
                    hostname = ?,
                    port = ?,
                    interval = ?,
                    retry_interval = ?,
                    maxretries = ?,
                    ignore_tls = ?,
                    accepted_statuscodes_json = ?,
                    description = ?,
                    active = 1
                WHERE id = ?
            """, (
                m["type"], m["url"], m["hostname"], m["port"],
                m["interval"], m["retry_interval"], m["maxretries"],
                m["ignore_tls"], m["accepted_statuscodes_json"], m["description"],
                mon_id
            ))
            updated += 1
            print(f"  [~] Sonde mise à jour : {m['name']} (id={mon_id})")
        else:
            cursor.execute("""
                INSERT INTO monitor (
                    name, type, url, hostname, port,
                    interval, retry_interval, maxretries, ignore_tls,
                    accepted_statuscodes_json, description, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                m["name"], m["type"], m["url"], m["hostname"], m["port"],
                m["interval"], m["retry_interval"], m["maxretries"],
                m["ignore_tls"], m["accepted_statuscodes_json"], m["description"]
            ))
            inserted += 1
            print(f"  [+] Sonde créée : {m['name']} ({m['type'].upper()})")

    # Création optionnelle de la page de statut officielle de l'établissement
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='status_page';")
    if cursor.fetchone():
        cursor.execute("SELECT id FROM status_page WHERE slug = 'etat-services';")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO status_page (slug, title, description, icon, theme, published)
                VALUES ('etat-services', 'État des Services LyuX', 'Supervision temps réel de l infrastructure scolaire', '🐧', 'auto', 1);
            """)
            print("  [+] Page de statut publique créée : slug 'etat-services'")

    conn.commit()
    conn.close()
    print(f"[OK] Provisioning termine avec succes : {inserted} ajoutees, {updated} mises a jour.")
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else find_db()
    if not path:
        print("[X] Impossible de localiser kuma.db automatiquement.")
        print("Usage: python init_kuma_monitors.py <chemin_vers_kuma.db>")
        sys.exit(1)
    success = provision_monitors(path)
    sys.exit(0 if success else 1)
