#!/usr/bin/env bash
# ==============================================================================
# Script de configuration du stockage partagé (CIFS/NFS), des ACLs et des Quotas
# Projet : Opération Manchot (LyuX) - Jalons M2 (Features 8 & 9)
# Emplacement cible : projects/lyux-server-infra/scripts/setup-shares.sh
# ==============================================================================
set -euo pipefail

echo "======================================================================"
echo "🐧 LyuX : Déploiement du Stockage Partagé, des ACLs POSIX & des Quotas"
echo "======================================================================"

# 1. Vérification des privilèges d'administration
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "❌ Erreur : Ce script doit être exécuté en tant que root (sudo)." >&2
    exit 1
fi

BASE_STORAGE="/srv/samba"
EXPORTS_DIR="/etc/exports.d"
EXPORTS_FILE="${EXPORTS_DIR}/lyux.exports"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPORTS_TEMPLATE="${SCRIPT_DIR}/../configs/samba/exports.template"

# Définition des quotas disques (en Ko / 1024 octets par bloc)
# 5 Go = 5 * 1024 * 1024 = 5 242 880 Ko
# 20 Go = 20 * 1024 * 1024 = 20 971 520 Ko
QUOTA_ELEVES_KB=5242880
QUOTA_PROFS_KB=20971520

# ------------------------------------------------------------------------------
# Étape 1 : Création et vérification des groupes système requis
# ------------------------------------------------------------------------------
echo "👥 1. Vérification des groupes POSIX standards..."
getent group eleves >/dev/null || groupadd -g 2000 eleves
getent group enseignants >/dev/null || groupadd -g 2001 enseignants
getent group administration >/dev/null || groupadd -g 2002 administration
getent group viesco >/dev/null || groupadd -g 2003 viesco
getent group techniciens >/dev/null || groupadd -g 2004 techniciens

# Groupes de classes pédagogiques pilotes (optionnels ou alias)
getent group 1g1 >/dev/null || groupadd 1g1 2>/dev/null || true
getent group 1g2 >/dev/null || groupadd 1g2 2>/dev/null || true

# ------------------------------------------------------------------------------
# Étape 2 : Création de l'arborescence des partages
# ------------------------------------------------------------------------------
echo "📁 2. Création de l'arborescence des dossiers partagés sous /srv/samba..."

mkdir -p /srv/samba/homes
mkdir -p /srv/samba/classes/1G1_B204/Distribution
mkdir -p /srv/samba/classes/1G1_B204/Depot
mkdir -p /srv/samba/classes/1G2_S102/Distribution
mkdir -p /srv/samba/classes/1G2_S102/Depot
mkdir -p /srv/samba/profs
mkdir -p /srv/samba/administration
mkdir -p /srv/samba/commun
mkdir -p /srv/backups/daily

# Permissions de base
chmod 755 /srv/samba
chmod 755 /srv/samba/homes
chmod 755 /srv/samba/classes
chmod 755 /srv/samba/classes/1G1_B204
chmod 755 /srv/samba/classes/1G2_S102

chown root:root /srv/samba
chown root:root /srv/samba/homes
chown root:enseignants /srv/samba/classes
chown root:enseignants /srv/samba/classes/1G1_B204
chown root:enseignants /srv/samba/classes/1G2_S102

# ------------------------------------------------------------------------------
# Étape 3 : Application des ACLs POSIX fines (Distribution vs Dépôt)
# ------------------------------------------------------------------------------
echo "🔒 3. Application des ACLs POSIX fines (setfacl)..."

if ! command -v setfacl >/dev/null 2>&1; then
    echo "⚠️ setfacl non trouvé. Installation du paquet acl..."
    apt-get update -qq && apt-get install -y acl
fi

CLASSES=("1G1_B204" "1G2_S102")

for CLS in "${CLASSES[@]}"; do
    DIST_DIR="/srv/samba/classes/${CLS}/Distribution"
    DEPOT_DIR="/srv/samba/classes/${CLS}/Depot"

    echo "   📂 Configuration de la salle ${CLS}..."

    # --- A. DISTRIBUTION (Enseignants: RWX, Élèves: R-X / Lecture Seule) ---
    chown -R root:enseignants "$DIST_DIR"
    chmod 2755 "$DIST_DIR"
    setfacl -b "$DIST_DIR" 2>/dev/null || true

    # ACLs actives sur le répertoire
    setfacl -m u::rwx,g::r-x,o::--- "$DIST_DIR"
    setfacl -m g:enseignants:rwx "$DIST_DIR"
    setfacl -m g:eleves:r-x "$DIST_DIR"

    # ACLs par défaut héritées par tout nouveau fichier/sous-dossier créé
    setfacl -d -m u::rwx,g::r-x,o::--- "$DIST_DIR"
    setfacl -d -m g:enseignants:rwx "$DIST_DIR"
    setfacl -d -m g:eleves:r-x "$DIST_DIR"

    # --- B. DÉPÔT / DROP-BOX (Enseignants: RWX, Élèves: -WX avec Sticky Bit) ---
    # Sticky bit (+t) empêche un élève d'écraser ou supprimer le devoir d'un camarade
    # Pas de droit 'r' pour les élèves : interdit de lister ou d'espionner les dépôts des autres
    chown -R root:enseignants "$DEPOT_DIR"
    chmod 1773 "$DEPOT_DIR"
    setfacl -b "$DEPOT_DIR" 2>/dev/null || true

    # ACLs actives sur le répertoire de dépôt
    setfacl -m u::rwx,g::rwx,o::--- "$DEPOT_DIR"
    setfacl -m g:enseignants:rwx "$DEPOT_DIR"
    setfacl -m g:eleves:-wx "$DEPOT_DIR"
    chmod +t "$DEPOT_DIR"

    # ACLs par défaut sur les devoirs déposés :
    # Les enseignants ont rwx pour lire, corriger et annoter
    setfacl -d -m u::rwx,g::---,o::--- "$DEPOT_DIR"
    setfacl -d -m g:enseignants:rwx "$DEPOT_DIR"
    # Les autres élèves n'ont AUCUN droit sur les copies d'autrui
    setfacl -d -m g:eleves:--- "$DEPOT_DIR"
    setfacl -d -m o::--- "$DEPOT_DIR"
done

# --- C. Espace Profs (/srv/samba/profs) ---
echo "   📂 Configuration de l'espace Enseignants..."
chown -R root:enseignants /srv/samba/profs
chmod 2770 /srv/samba/profs
setfacl -b /srv/samba/profs 2>/dev/null || true
setfacl -m u::rwx,g::rwx,o::--- /srv/samba/profs
setfacl -m g:enseignants:rwx,g:techniciens:rwx,g:eleves:--- /srv/samba/profs
setfacl -d -m u::rwx,g::rwx,o::--- /srv/samba/profs
setfacl -d -m g:enseignants:rwx,g:techniciens:rwx,g:eleves:--- /srv/samba/profs

# --- D. Espace Administration (/srv/samba/administration) ---
echo "   📂 Configuration de l'espace Administration / Vie Scolaire..."
chown -R root:administration /srv/samba/administration
chmod 2770 /srv/samba/administration
setfacl -b /srv/samba/administration 2>/dev/null || true
setfacl -m u::rwx,g::rwx,o::--- /srv/samba/administration
setfacl -m g:administration:rwx,g:viesco:rwx,g:techniciens:rwx,g:eleves:---,g:enseignants:--- /srv/samba/administration
setfacl -d -m u::rwx,g::rwx,o::--- /srv/samba/administration
setfacl -d -m g:administration:rwx,g:viesco:rwx,g:techniciens:rwx,g:eleves:---,g:enseignants:--- /srv/samba/administration

# --- E. Espace Commun (/srv/samba/commun) ---
echo "   📂 Configuration de l'espace Public Commun..."
chown -R root:enseignants /srv/samba/commun
chmod 755 /srv/samba/commun
setfacl -b /srv/samba/commun 2>/dev/null || true
setfacl -m u::rwx,g::r-x,o::r-x /srv/samba/commun
setfacl -m g:enseignants:rwx,g:administration:rwx,g:techniciens:rwx,g:eleves:r-x /srv/samba/commun
setfacl -d -m u::rwx,g::r-x,o::r-x /srv/samba/commun
setfacl -d -m g:enseignants:rwx,g:administration:rwx,g:techniciens:rwx,g:eleves:r-x /srv/samba/commun

# ------------------------------------------------------------------------------
# Étape 4 : Déploiement et activation des Exports NFS
# ------------------------------------------------------------------------------
echo "📡 4. Configuration des exports NFS (/etc/exports.d/lyux.exports)..."
mkdir -p "${EXPORTS_DIR}"

if [ -f "${EXPORTS_TEMPLATE}" ]; then
    cp "${EXPORTS_TEMPLATE}" "${EXPORTS_FILE}"
else
    cat << 'EOF' > "${EXPORTS_FILE}"
# Exports NFS LyuX (Opération Manchot)
/srv/samba/homes          192.168.100.0/24(rw,sync,no_subtree_check,root_squash)
/srv/samba/classes        192.168.100.0/24(rw,sync,no_subtree_check,root_squash)
/srv/samba/profs          192.168.100.0/24(rw,sync,no_subtree_check,root_squash)
/srv/samba/administration 192.168.100.0/24(rw,sync,no_subtree_check,root_squash)
/srv/samba/commun         192.168.100.0/24(ro,sync,no_subtree_check,all_squash)
EOF
fi
chmod 644 "${EXPORTS_FILE}"

if command -v exportfs >/dev/null 2>&1; then
    exportfs -ra 2>/dev/null || echo "ℹ️ NFS server non démarré (mise à jour prise en compte au démarrage)."
fi

# ------------------------------------------------------------------------------
# Étape 5 : Configuration et application des Quotas Disques (5 Go Élèves / 20 Go Profs)
# ------------------------------------------------------------------------------
echo "💾 5. Configuration des quotas disques système (5 Go élèves, 20 Go profs)..."

STORAGE_DEV=$(df -P "${BASE_STORAGE}" 2>/dev/null | awk 'NR==2 {print $6}')

if command -v quotaon >/dev/null 2>&1 && [ -n "${STORAGE_DEV}" ]; then
    quotaon -v -aug "${STORAGE_DEV}" 2>/dev/null || true
fi

if command -v setquota >/dev/null 2>&1 && [ -n "${STORAGE_DEV}" ]; then
    # Application des quotas de groupe par défaut
    setquota -g eleves "${QUOTA_ELEVES_KB}" "${QUOTA_ELEVES_KB}" 0 0 "${STORAGE_DEV}" 2>/dev/null || true
    setquota -g enseignants "${QUOTA_PROFS_KB}" "${QUOTA_PROFS_KB}" 0 0 "${STORAGE_DEV}" 2>/dev/null || true
    setquota -g administration "${QUOTA_PROFS_KB}" "${QUOTA_PROFS_KB}" 0 0 "${STORAGE_DEV}" 2>/dev/null || true
    setquota -g viesco "${QUOTA_PROFS_KB}" "${QUOTA_PROFS_KB}" 0 0 "${STORAGE_DEV}" 2>/dev/null || true

    # Application des quotas pour les 8 comptes de test obligatoires
    for USER in lucas.martin emma.bernard hugo.dubois lea.thomas; do
        if id "$USER" >/dev/null 2>&1; then
            setquota -u "$USER" "${QUOTA_ELEVES_KB}" "${QUOTA_ELEVES_KB}" 0 0 "${STORAGE_DEV}" 2>/dev/null || true
        fi
    done

    for USER in thomas.durand sophie.leroy claire.viesco alain.direction; do
        if id "$USER" >/dev/null 2>&1; then
            setquota -u "$USER" "${QUOTA_PROFS_KB}" "${QUOTA_PROFS_KB}" 0 0 "${STORAGE_DEV}" 2>/dev/null || true
        fi
    done
fi

# Installation du script utilitaire de gestion de quota individuel
cat << 'EOF' > /usr/local/bin/lyux-set-quota.sh
#!/usr/bin/env bash
# lyux-set-quota.sh : Outil d'application et de consultation des quotas LyuX
set -euo pipefail

USER_NAME="${1:-}"
TARGET_ROLE="${2:-eleves}" # eleves | enseignants

if [ -z "$USER_NAME" ]; then
    echo "Usage : lyux-set-quota.sh <username> [eleves|enseignants]"
    exit 1
fi

STORAGE_DEV=$(df -P /srv/samba 2>/dev/null | awk 'NR==2 {print $6}')

if [ "$TARGET_ROLE" = "eleves" ]; then
    LIMIT_KB=5242880 # 5 Go
else
    LIMIT_KB=20971520 # 20 Go
fi

if command -v setquota >/dev/null 2>&1; then
    setquota -u "$USER_NAME" "$LIMIT_KB" "$LIMIT_KB" 0 0 "$STORAGE_DEV" 2>/dev/null || true
    echo "✅ Quota défini pour $USER_NAME : $(($LIMIT_KB / 1024 / 1024)) Go."
else
    echo "ℹ️ Commande setquota absente."
fi
EOF
chmod +x /usr/local/bin/lyux-set-quota.sh

# ------------------------------------------------------------------------------
# Étape 6 : Mise à jour du helper dynamique de création des Homes (/usr/local/bin/lyux-create-user-home.sh)
# ------------------------------------------------------------------------------
echo "🛠️ 6. Mise à jour du script de création dynamique de homes..."
cat << 'EOF' > /usr/local/bin/lyux-create-user-home.sh
#!/bin/bash
USER_NAME="$1"
USER_GROUP="$2"
USER_HOME="/srv/samba/homes/$USER_NAME"

if [ ! -d "$USER_HOME" ]; then
    mkdir -p "$USER_HOME"
    mkdir -p "$USER_HOME/Documents" "$USER_HOME/Images" "$USER_HOME/Bureau"
    chown -R "$USER_NAME:$USER_GROUP" "$USER_HOME"
    chmod 700 "$USER_HOME"

    # Application automatique du quota disque selon le profil
    STORAGE_DEV=$(df -P "$USER_HOME" 2>/dev/null | awk 'NR==2 {print $6}')
    if [ -n "$STORAGE_DEV" ] && command -v setquota >/dev/null 2>&1; then
        if [ "$USER_GROUP" = "eleves" ]; then
            setquota -u "$USER_NAME" 5242880 5242880 0 0 "$STORAGE_DEV" 2>/dev/null || true
        elif [ "$USER_GROUP" = "enseignants" ] || [ "$USER_GROUP" = "administration" ] || [ "$USER_GROUP" = "viesco" ]; then
            setquota -u "$USER_NAME" 20971520 20971520 0 0 "$STORAGE_DEV" 2>/dev/null || true
        fi
    fi
fi
EOF
chmod +x /usr/local/bin/lyux-create-user-home.sh

echo "======================================================================"
echo "✅ Configuration du stockage partagé et des quotas terminée avec succès !"
echo "======================================================================"
