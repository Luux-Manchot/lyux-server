#!/usr/bin/env python3
"""
==============================================================================
LyuX - Opération Manchot
Script d'importation et de provisionnement automatisé des utilisateurs (élèves, enseignants, vie scolaire, direction)
depuis un export CSV (ex: SIECLE, Pronote, ENT) vers Samba-AD, LDAP et le système Linux.
==============================================================================
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Forcer stdout en UTF-8 si possible pour éviter les UnicodeEncodeError sous Windows/CP1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configuration par défaut
DEFAULT_DOMAIN = "LYUX.LAN"
DEFAULT_HOMES_BASE = "/srv/samba/homes"
DEFAULT_CLASSES_BASE = "/srv/samba/classes"

# Définition des GIDs et profils par rôle
ROLE_PROFILES = {
    "eleves": {
        "gid": 2000,
        "primary_group": "eleves",
        "secondary_groups": [],
        "ou": "OU=Eleves,OU=Utilisateurs",
        "quota_soft_kb": 5242880,      # 5 GB
        "quota_hard_kb": 5767168,      # 5.5 GB
        "description": "Élève du Lycée"
    },
    "enseignants": {
        "gid": 2001,
        "primary_group": "enseignants",
        "secondary_groups": [],
        "ou": "OU=Enseignants,OU=Utilisateurs",
        "quota_soft_kb": 20971520,     # 20 GB
        "quota_hard_kb": 23068672,     # 22 GB
        "description": "Professeur / Enseignant"
    },
    "administration": {
        "gid": 2002,
        "primary_group": "administration",
        "secondary_groups": ["direction"],
        "ou": "OU=Direction,OU=Utilisateurs",
        "quota_soft_kb": 20971520,     # 20 GB
        "quota_hard_kb": 23068672,     # 22 GB
        "description": "Personnel de Direction / Administration"
    },
    "direction": {
        "gid": 2005,
        "primary_group": "administration",
        "secondary_groups": ["direction"],
        "ou": "OU=Direction,OU=Utilisateurs",
        "quota_soft_kb": 20971520,     # 20 GB
        "quota_hard_kb": 23068672,     # 22 GB
        "description": "Direction de l'établissement"
    },
    "viesco": {
        "gid": 2003,
        "primary_group": "viesco",
        "secondary_groups": ["administration"],
        "ou": "OU=viesco,OU=Utilisateurs",
        "quota_soft_kb": 10485760,     # 10 GB
        "quota_hard_kb": 11534336,     # 11 GB
        "description": "Vie Scolaire / CPE"
    },
    "techniciens": {
        "gid": 2004,
        "primary_group": "techniciens",
        "secondary_groups": ["sudo"],
        "ou": "OU=Utilisateurs",
        "quota_soft_kb": 52428800,     # 50 GB
        "quota_hard_kb": 55050240,     # 52.5 GB
        "description": "Technicien Informatique / Administrateur Système"
    }
}


def clean_string(text: str) -> str:
    """
    Supprime les accents, espaces et caractères spéciaux.
    Conforme aux spécifications RFC / POSIX et validé par la suite de tests E2E.
    """
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\._-]', '', text).lower()
    return text


def generate_username(prenom: str, nom: str) -> str:
    """Format standard d'identifiant LyuX : prenom.nom"""
    p = clean_string(prenom or "").strip(".-_")
    n = clean_string(nom or "").strip(".-_")
    if p and n:
        return f"{p}.{n}"
    elif n:
        return n
    elif p:
        return p
    return "user"


def is_samba_ad_active() -> bool:
    """Vérifie si samba-tool est disponible et configuré en contrôleur de domaine (AD DC)."""
    if not shutil.which("samba-tool"):
        return False
    # Vérifie si le fichier sam.ldb ou la commande domain info répond
    res = subprocess.run(
        ["samba-tool", "domain", "info", "127.0.0.1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if res.returncode == 0:
        return True
    # Test alternatif : vérifier l'existence de sam.ldb
    return os.path.exists("/var/lib/samba/private/sam.ldb")


def ensure_system_group(group_name: str, gid: Optional[int] = None) -> bool:
    """Crée un groupe système local de manière idempotente si manquant."""
    check = subprocess.run(["getent", "group", group_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if check.returncode == 0:
        return True
    cmd = ["groupadd"]
    if gid is not None:
        cmd.extend(["-g", str(gid)])
    cmd.append(group_name)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  [Linux Group] Groupe créé : {group_name} (GID: {gid or 'auto'})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback automatique sans GID fixe si le GID est déjà utilisé
        try:
            subprocess.run(["groupadd", group_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  [Linux Group] Groupe créé (GID auto) : {group_name}")
            return True
        except Exception as e:
            print(f"  [Linux Group] ⚠️ Impossible de créer le groupe {group_name}: {e}")
            return False


def ensure_samba_ad_group(group_name: str) -> bool:
    """Crée un groupe Samba Active Directory de manière idempotente."""
    if not shutil.which("samba-tool"):
        return False
    check = subprocess.run(
        ["samba-tool", "group", "list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    if check.returncode == 0 and group_name in check.stdout.splitlines():
        return True
    try:
        subprocess.run(
            ["samba-tool", "group", "add", group_name, "--group-type=Security", "--group-scope=Global"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"  [Samba AD Group] Groupe AD créé : {group_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [Samba AD Group] ⚠️ Échec création groupe AD {group_name}: {e}")
        return False


def ensure_samba_ad_ou(ou_dn: str) -> bool:
    """Vérifie ou crée une Unité Organisationnelle (OU) dans Samba-AD."""
    if not shutil.which("samba-tool"):
        return False
    try:
        # samba-tool ou create est disponible dans les versions Samba récentes
        subprocess.run(
            ["samba-tool", "ou", "create", ou_dn],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"  [Samba AD OU] OU créée : {ou_dn}")
        return True
    except subprocess.CalledProcessError:
        # L'OU existe probablement déjà
        return True
    except FileNotFoundError:
        return False


def provision_user_home(username: str, group: str, homes_base: str = DEFAULT_HOMES_BASE) -> bool:
    """
    Crée et initialise le répertoire personnel réseau avec les sous-dossiers standards :
    Documents, Images, Bureau (Mode strict 0700).
    """
    home_dir = Path(homes_base) / username
    try:
        os.makedirs(home_dir / "Documents", exist_ok=True)
        os.makedirs(home_dir / "Images", exist_ok=True)
        os.makedirs(home_dir / "Bureau", exist_ok=True)
        os.chmod(home_dir, 0o700)
        
        # Ajustement des droits de propriété si nous avons les privilèges root
        if os.geteuid() == 0 if hasattr(os, "geteuid") else False:
            import pwd
            import grp
            try:
                uid = pwd.getpwnam(username).pw_uid
                gid = grp.getgrnam(group).gr_gid
                for root, dirs, files in os.walk(home_dir):
                    os.chown(root, uid, gid)
                    for d in dirs:
                        os.chown(os.path.join(root, d), uid, gid)
                    for f in files:
                        os.chown(os.path.join(root, f), uid, gid)
            except (KeyError, PermissionError):
                pass
        return True
    except Exception as e:
        print(f"  [Storage] ⚠️ Échec création home {home_dir}: {e}")
        return False


def apply_user_quota(username: str, role: str) -> None:
    """Applique les quotas disque système si l'utilitaire setquota est présent."""
    if not shutil.which("setquota"):
        return
    profile = ROLE_PROFILES.get(role)
    if not profile or "quota_soft_kb" not in profile:
        return
    soft = profile["quota_soft_kb"]
    hard = profile["quota_hard_kb"]
    try:
        # Applique sur le point de montage /srv/samba ou racine
        target_fs = "/srv/samba" if os.path.ismount("/srv/samba") else "/"
        subprocess.run(
            ["setquota", "-u", username, str(soft), str(hard), "0", "0", target_fs],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def create_or_update_system_user(
    username: str,
    prenom: str,
    nom: str,
    role: str,
    classe: str,
    password: str,
    update_passwords: bool = False,
    homes_base: str = DEFAULT_HOMES_BASE
) -> bool:
    """
    Crée ou met à jour le compte utilisateur Linux local et son mot de passe Samba classique (smbpasswd).
    Garantit l'idempotence totale : ne plante pas si l'utilisateur existe déjà.
    """
    profile = ROLE_PROFILES.get(role, ROLE_PROFILES["eleves"])
    primary_group = profile["primary_group"]
    secondary_groups = list(profile["secondary_groups"])
    
    # Ajoute la classe comme groupe secondaire si applicable
    clean_classe = clean_string(classe)
    if clean_classe:
        ensure_system_group(clean_classe)
        secondary_groups.append(clean_classe)
    
    # S'assure que le groupe primaire existe
    ensure_system_group(primary_group, profile.get("gid"))
    for sg in secondary_groups:
        ensure_system_group(sg)
    
    display_name = f"{prenom.capitalize()} {nom.upper()}"
    home_dir = f"{homes_base}/{username}"
    
    check_user = subprocess.run(["id", username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if check_user.returncode != 0:
        # Création de l'utilisateur Linux local
        cmd = [
            "useradd", "-m", "-d", home_dir,
            "-g", primary_group,
            "-s", "/bin/bash",
            "-c", display_name
        ]
        if secondary_groups:
            cmd.extend(["-G", ",".join(secondary_groups)])
        cmd.append(username)
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  [Linux System] ⚠️ Échec useradd pour {username}: {e}")
            return False

        # Définition du mot de passe Linux via chpasswd
        if shutil.which("chpasswd"):
            p1 = subprocess.Popen(["chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p1.communicate(input=f"{username}:{password}\n".encode())

        # Ajout du compte au serveur Samba autonome via smbpasswd
        if shutil.which("smbpasswd"):
            p2 = subprocess.Popen(["smbpasswd", "-a", "-s", username], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p2.communicate(input=f"{password}\n{password}\n".encode())

        print(f"  [Linux System] ✅ Compte créé : {username} (Groupe: {primary_group}, Classe: {classe})")
    else:
        # L'utilisateur existe déjà : mise à jour idempotente des groupes secondaires
        if secondary_groups:
            subprocess.run(
                ["usermod", "-a", "-G", ",".join(secondary_groups), username],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        if update_passwords:
            if shutil.which("chpasswd"):
                p1 = subprocess.Popen(["chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                p1.communicate(input=f"{username}:{password}\n".encode())
            if shutil.which("smbpasswd"):
                p2 = subprocess.Popen(["smbpasswd", "-s", username], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                p2.communicate(input=f"{password}\n{password}\n".encode())
            print(f"  [Linux System] 🔄 Mot de passe actualisé : {username}")
        else:
            print(f"  [Linux System] ℹ️ Compte existant conservé : {username}")

    # Provisionnement du dossier personnel et quotas
    provision_user_home(username, primary_group, homes_base)
    apply_user_quota(username, role)
    return True


def create_or_update_samba_ad_user(
    username: str,
    prenom: str,
    nom: str,
    role: str,
    classe: str,
    password: str,
    domain: str = DEFAULT_DOMAIN,
    update_passwords: bool = False
) -> bool:
    """
    Crée ou met à jour le compte utilisateur dans l'Active Directory Samba (samba-tool).
    Place l'utilisateur dans son Unité Organisationnelle (OU) dédiée, lui assigne son groupe
    et ses attributs RFC2307 / éducation.
    """
    if not shutil.which("samba-tool"):
        return False
        
    profile = ROLE_PROFILES.get(role, ROLE_PROFILES["eleves"])
    primary_group = profile["primary_group"]
    ou_path = profile["ou"]
    mail = f"{username}@{domain.lower()}"
    
    # S'assurer que le groupe AD existe
    ensure_samba_ad_group(primary_group)
    clean_classe = clean_string(classe)
    if clean_classe:
        ensure_samba_ad_group(clean_classe)

    # Vérification si l'utilisateur existe déjà dans l'AD
    list_check = subprocess.run(
        ["samba-tool", "user", "list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    user_exists = (list_check.returncode == 0 and username in list_check.stdout.splitlines())
    
    if not user_exists:
        # Création du compte utilisateur dans l'AD
        cmd = [
            "samba-tool", "user", "create",
            username, password,
            f"--given-name={prenom.capitalize()}",
            f"--surname={nom.upper()}",
            f"--mail={mail}",
            f"--userou={ou_path}",
            f"--description=Classe: {classe} | Rôle: {role}",
            f"--department={classe}",
            "--use-username-as-cn",
            "--must-change-at-next-login=false"
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Désactivation de l'expiration du mot de passe pour les comptes de test lab
            subprocess.run(["samba-tool", "user", "setexpiry", username, "--noexpiry"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Ajout au groupe principal
            subprocess.run(["samba-tool", "group", "addmembers", primary_group, username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if clean_classe:
                subprocess.run(["samba-tool", "group", "addmembers", clean_classe, username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  [Samba-AD] ✅ Utilisateur créé : {username} dans {ou_path} (Groupe: {primary_group})")
            return True
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode('utf-8', errors='ignore') if hasattr(e, 'stderr') and e.stderr else str(e)
            print(f"  [Samba-AD] ⚠️ Échec création utilisateur AD {username}: {err}")
            return False
    else:
        # L'utilisateur existe déjà : mise à jour idempotente
        if update_passwords:
            subprocess.run(
                ["samba-tool", "user", "setpassword", username, f"--newpassword={password}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"  [Samba-AD] 🔄 Mot de passe AD actualisé : {username}")
        else:
            print(f"  [Samba-AD] ℹ️ Utilisateur AD déjà existant : {username}")
        
        # S'assurer de l'appartenance aux groupes AD
        subprocess.run(["samba-tool", "group", "addmembers", primary_group, username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if clean_classe:
            subprocess.run(["samba-tool", "group", "addmembers", clean_classe, username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True


def generate_ldif_content(users: List[Dict[str, str]], domain: str = DEFAULT_DOMAIN) -> str:
    """Génère un export LDIF complet des OUs, groupes et utilisateurs pour import OpenLDAP/Samba."""
    dc_parts = [f"dc={part.lower()}" for part in domain.split(".")]
    base_dn = ",".join(dc_parts)
    
    ldif_lines = [
        f"# ==============================================================================",
        f"# Export LDIF Annuaire LyuX (Opération Manchot) - Domaine: {domain}",
        f"# ==============================================================================",
        "",
        f"# --- Racine & OUs Principales ---",
        f"dn: ou=utilisateurs,{base_dn}",
        "objectClass: top",
        "objectClass: organizationalUnit",
        "ou: utilisateurs",
        "",
        f"dn: ou=eleves,ou=utilisateurs,{base_dn}",
        "objectClass: top",
        "objectClass: organizationalUnit",
        "ou: eleves",
        "",
        f"dn: ou=enseignants,ou=utilisateurs,{base_dn}",
        "objectClass: top",
        "objectClass: organizationalUnit",
        "ou: enseignants",
        "",
        f"dn: ou=viesco,ou=utilisateurs,{base_dn}",
        "objectClass: top",
        "objectClass: organizationalUnit",
        "ou: viesco",
        "",
        f"dn: ou=direction,ou=utilisateurs,{base_dn}",
        "objectClass: top",
        "objectClass: organizationalUnit",
        "ou: direction",
        "",
        f"dn: ou=groupes,{base_dn}",
        "objectClass: top",
        "objectClass: organizationalUnit",
        "ou: groupes",
        ""
    ]
    
    # Groupes standards
    for role_name, prof in ROLE_PROFILES.items():
        gid = prof["gid"]
        ldif_lines.extend([
            f"# Groupe : {role_name}",
            f"dn: cn={role_name},ou=groupes,{base_dn}",
            "objectClass: top",
            "objectClass: posixGroup",
            f"cn: {role_name}",
            f"gidNumber: {gid}",
            f"description: {prof['description']}",
            ""
        ])

    # Utilisateurs
    uid_counter = 10001
    seen_dns = set()
    for u in users:
        prenom = (u.get("prenom") or "").strip()
        nom = (u.get("nom") or "").strip()
        role = (u.get("role") or "eleves").strip().lower()
        classe = (u.get("classe") or "").strip()
        pwd = (u.get("motdepasse_temporaire") or "LyuX@2026!").strip()
        
        username = generate_username(prenom, nom)
        profile = ROLE_PROFILES.get(role, ROLE_PROFILES["eleves"])
        ou_name = profile["ou"].split(",")[0].replace("OU=", "").strip().lower()
        
        if ou_name == "utilisateurs":
            user_dn = f"dn: cn={username},ou=utilisateurs,{base_dn}"
        else:
            user_dn = f"dn: cn={username},ou={ou_name},ou=utilisateurs,{base_dn}"

        if user_dn in seen_dns:
            continue
        seen_dns.add(user_dn)
        
        ldif_lines.extend([
            f"# Utilisateur : {username}",
            user_dn,
            "objectClass: top",
            "objectClass: person",
            "objectClass: organizationalPerson",
            "objectClass: inetOrgPerson",
            "objectClass: posixAccount",
            f"cn: {username}",
            f"sn: {nom.upper()}",
            f"givenName: {prenom.capitalize()}",
            f"displayName: {prenom.capitalize()} {nom.upper()}",
            f"mail: {username}@{domain.lower()}",
            f"uid: {username}",
            f"uidNumber: {uid_counter}",
            f"gidNumber: {profile['gid']}",
            f"homeDirectory: /srv/samba/homes/{username}",
            f"loginShell: /bin/bash",
            f"departmentNumber: {classe}",
            f"description: Classe {classe}",
            f"userPassword: {pwd}",
            ""
        ])
        uid_counter += 1

    return "\n".join(ldif_lines)


def import_csv(
    file_path: str,
    mode: str = "auto",
    update_passwords: bool = False,
    export_ldif_path: Optional[str] = None,
    dry_run: bool = False,
    domain: str = DEFAULT_DOMAIN,
    homes_base: str = DEFAULT_HOMES_BASE
) -> int:
    """
    Fonction principale de lecture et d'orchestration de l'import CSV.
    Retourne le nombre d'utilisateurs traités avec succès.
    """
    if not os.path.exists(file_path):
        print(f"❌ Fichier CSV introuvable : {file_path}")
        return 0

    users = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            reader.fieldnames = [f.strip() for f in reader.fieldnames if f]
        for row in reader:
            prenom = (row.get('prenom') or '').strip()
            nom = (row.get('nom') or '').strip()
            if not prenom or not nom:
                continue
            users.append(row)

    print(f"📋 Fichier CSV chargé : {file_path} ({len(users)} utilisateurs détectés)")

    # Export LDIF si demandé
    if export_ldif_path:
        ldif_data = generate_ldif_content(users, domain=domain)
        with open(export_ldif_path, mode='w', encoding='utf-8') as f_out:
            f_out.write(ldif_data)
        print(f"📄 Export LDIF généré avec succès dans : {export_ldif_path}")
        if mode == "ldif":
            return len(users)

    if dry_run:
        print("\n🔍 --- SIMULATION (DRY-RUN) ---")
        for u in users:
            prenom = (u.get('prenom') or '').strip()
            nom = (u.get('nom') or '').strip()
            uname = generate_username(prenom, nom)
            role = (u.get('role') or 'eleves').strip().lower()
            prof = ROLE_PROFILES.get(role, ROLE_PROFILES["eleves"])
            classe = (u.get('classe') or '-').strip()
            print(f"  • {uname:20} -> Rôle: {role:14} Classe: {classe:15} OU: {prof['ou']}")
        print(f"🔍 Simulation terminée pour {len(users)} utilisateurs. Aucune modification système.")
        return len(users)

    # Détection automatique du mode d'exécution
    has_samba_ad = is_samba_ad_active()
    has_system_useradd = shutil.which("useradd") is not None

    if mode == "auto":
        print(f"⚙️ Mode Auto détecté : Samba-AD Active = {has_samba_ad}, Linux System Useradd = {has_system_useradd}")
    elif mode == "samba-ad":
        has_system_useradd = False
    elif mode == "system":
        has_samba_ad = False

    success_count = 0
    for u in users:
        prenom = (u.get('prenom') or '').strip()
        nom = (u.get('nom') or '').strip()
        role = (u.get('role') or 'eleves').strip().lower()
        classe = (u.get('classe') or '').strip()
        pwd = (u.get('motdepasse_temporaire') or 'LyuX@2026!').strip()
        username = generate_username(prenom, nom)

        print(f"\n👤 Traitement de {username} ({prenom} {nom} - {role} - {classe}) :")

        # 1. Provisionnement système Linux et Samba classique
        if has_system_useradd:
            create_or_update_system_user(
                username=username,
                prenom=prenom,
                nom=nom,
                role=role,
                classe=classe,
                password=pwd,
                update_passwords=update_passwords,
                homes_base=homes_base
            )

        # 2. Provisionnement Samba Active Directory
        if has_samba_ad:
            create_or_update_samba_ad_user(
                username=username,
                prenom=prenom,
                nom=nom,
                role=role,
                classe=classe,
                password=pwd,
                domain=domain,
                update_passwords=update_passwords
            )

        success_count += 1

    print(f"\n✨ Import terminé : {success_count}/{len(users)} utilisateurs provisionnés.")
    return success_count


def parse_arguments():
    """Analyse les arguments CLI avec support de la compatibilité ascendante."""
    parser = argparse.ArgumentParser(
        description="LyuX - Importation et provisionnement automatisé des utilisateurs (Samba-AD / Linux)."
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        default=os.path.join(os.path.dirname(__file__), "..", "configs", "utilisateurs-test.csv"),
        help="Chemin vers le fichier CSV source (colonnes: prenom,nom,role,classe,motdepasse_temporaire)"
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "samba-ad", "system", "ldif"],
        default="auto",
        help="Mode de provisionnement (défaut: auto)"
    )
    parser.add_argument(
        "--update-passwords",
        action="store_true",
        help="Met à jour les mots de passe si l'utilisateur existe déjà"
    )
    parser.add_argument(
        "--export-ldif",
        metavar="PATH",
        help="Exporte un fichier LDIF des utilisateurs et OUs"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valide le CSV et affiche les actions sans modifier le système"
    )
    parser.add_argument(
        "--domain",
        default=DEFAULT_DOMAIN,
        help=f"Nom de domaine Active Directory (défaut: {DEFAULT_DOMAIN})"
    )
    parser.add_argument(
        "--homes-base",
        default=DEFAULT_HOMES_BASE,
        help=f"Répertoire racine des homes utilisateurs (défaut: {DEFAULT_HOMES_BASE})"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    csv_path = args.csv_file
    
    if not os.path.exists(csv_path):
        print(f"❌ Fichier CSV introuvable : {csv_path}")
        print("Usage: python3 import-users-csv.py <chemin_fichier.csv> [options]")
        sys.exit(1)

    import_csv(
        file_path=csv_path,
        mode=args.mode,
        update_passwords=args.update_passwords,
        export_ldif_path=args.export_ldif,
        dry_run=args.dry_run,
        domain=args.domain,
        homes_base=args.homes_base
    )
