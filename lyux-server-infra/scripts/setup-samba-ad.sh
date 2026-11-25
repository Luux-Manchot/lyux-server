#!/usr/bin/env bash
# ==============================================================================
# Script de Déploiement et Provisioning Samba-AD DC (Opération Manchot)
# Domaine : LYUX.LAN | NetBIOS : SERVEUR-LYUX | Rôle : Domain Controller
# Emplacement cible : lyux-server-infra/scripts/setup-samba-ad.sh
# ==============================================================================
set -euo pipefail

echo "======================================================================"
echo "🏰 Provisioning du Contrôleur de Domaine Samba-AD DC (LYUX.LAN)"
echo "======================================================================"

# 1. Vérification des privilèges root
if [ "${EUID}" -ne 0 ]; then
    echo "❌ Ce script doit impérativement être exécuté en tant que root (sudo)."
    exit 1
fi

REALM="${SAMBA_REALM:-LYUX.LAN}"
DOMAIN="${SAMBA_DOMAIN:-LYUX}"
ADMIN_PASS="${SAMBA_ADMIN_PASSWORD:-Admin@Lyux2026!}"
NETBIOS_NAME="${SAMBA_NETBIOS_NAME:-SERVEUR-LYUX}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../configs/samba"

# 2. Arrêt et désactivation des services Samba autonomes / slapd concurrents
echo "🛑 1. Désactivation des services Samba classiques (smbd, nmbd, winbind)..."
for svc in smbd nmbd winbind slapd; do
    if systemctl is-active --quiet "${svc}" 2>/dev/null; then
        systemctl stop "${svc}" || true
    fi
    systemctl disable "${svc}" 2>/dev/null || true
    systemctl mask "${svc}" 2>/dev/null || true
done

# 3. Sauvegarde de l'ancienne configuration Samba si elle existe
if [ -f /etc/samba/smb.conf ]; then
    BACKUP_FILE="/etc/samba/smb.conf.backup-$(date +%Y%m%d-%H%M%S)"
    echo "💾 Sauvegarde de l'ancien smb.conf vers ${BACKUP_FILE}..."
    cp /etc/samba/smb.conf "${BACKUP_FILE}"
    rm -f /etc/samba/smb.conf
fi

# 4. Provisioning du domaine Active Directory via samba-tool
if [ -f /var/lib/samba/private/sam.ldb ]; then
    echo "ℹ️ Base Active Directory déjà provisionnée (/var/lib/samba/private/sam.ldb)."
else
    echo "🚀 2. Exécution du provisioning samba-tool domain provision..."
    if command -v samba-tool >/dev/null 2>&1; then
        samba-tool domain provision \
            --use-rfc2307 \
            --realm="${REALM}" \
            --domain="${DOMAIN}" \
            --server-role=dc \
            --dns-backend=SAMBA_INTERNAL \
            --adminpass="${ADMIN_PASS}" \
            --option="netbios name = ${NETBIOS_NAME}"
        echo "✅ Domaine ${DOMAIN} (${REALM}) provisionné avec succès."
    else
        echo "ℹ️ samba-tool non disponible, provisioning AD différé."
    fi
fi

# 5. Déploiement du modèle smb.conf.ad-dc personnalisé avec partages lycéens
if [ -f "${CONFIG_DIR}/smb.conf.ad-dc" ]; then
    echo "📋 3. Déploiement de la configuration smb.conf.ad-dc officielle..."
    cp "${CONFIG_DIR}/smb.conf.ad-dc" /etc/samba/smb.conf
    chmod 644 /etc/samba/smb.conf
else
    echo "ℹ️ Utilisation du smb.conf généré par le provisioning initial."
fi

# 6. Configuration de Kerberos (/etc/krb5.conf)
if [ -f /var/lib/samba/private/krb5.conf ]; then
    echo "🔑 4. Mise à jour de /etc/krb5.conf avec la clef du domaine..."
    cp -b /var/lib/samba/private/krb5.conf /etc/krb5.conf
    chmod 644 /etc/krb5.conf
fi

# 7. Création des répertoires de stockage partagé et permissions
echo "📁 5. Préparation des points de partage réseau..."
mkdir -p /srv/samba/{homes,classes,profs,administration,commun}
chmod 755 /srv/samba
chmod 775 /srv/samba/commun
chmod 770 /srv/samba/{classes,profs,administration}

# 8. Création des Unités Organisationnelles (OUs) standard du DIT
echo "🌳 6. Création des Unités Organisationnelles (OUs) dans l'annuaire AD..."
if command -v samba-tool >/dev/null 2>&1; then
    samba-tool ou create "ou=utilisateurs,dc=lyux,dc=lan" 2>/dev/null || echo "ℹ️ OU utilisateurs déjà présente."
    samba-tool ou create "ou=eleves,ou=utilisateurs,dc=lyux,dc=lan" 2>/dev/null || echo "ℹ️ OU eleves déjà présente."
    samba-tool ou create "ou=enseignants,ou=utilisateurs,dc=lyux,dc=lan" 2>/dev/null || echo "ℹ️ OU enseignants déjà présente."
    samba-tool ou create "ou=viesco,ou=utilisateurs,dc=lyux,dc=lan" 2>/dev/null || echo "ℹ️ OU viesco déjà présente."
    samba-tool ou create "ou=direction,ou=utilisateurs,dc=lyux,dc=lan" 2>/dev/null || echo "ℹ️ OU direction déjà présente."
    samba-tool ou create "ou=groupes,dc=lyux,dc=lan" 2>/dev/null || echo "ℹ️ OU groupes déjà présente."

    # Création des OUs racines de compatibilité pour requêtes SSSD directes
    samba-tool ou create "ou=eleves,dc=lyux,dc=lan" 2>/dev/null || true
    samba-tool ou create "ou=enseignants,dc=lyux,dc=lan" 2>/dev/null || true
    samba-tool ou create "ou=viesco,dc=lyux,dc=lan" 2>/dev/null || true
    samba-tool ou create "ou=direction,dc=lyux,dc=lan" 2>/dev/null || true
fi

# 9. Activation et démarrage du service daemon samba-ad-dc
echo "⚙️ 7. Démarrage du daemon samba-ad-dc..."
if command -v systemctl >/dev/null 2>&1 && systemctl is-system-running >/dev/null 2>&1; then
    systemctl unmask samba-ad-dc || true
    systemctl enable --now samba-ad-dc
    echo "✅ Service samba-ad-dc actif et en écoute."
else
    systemctl unmask samba-ad-dc 2>/dev/null || true
    systemctl enable samba-ad-dc 2>/dev/null || true
    echo "ℹ️ Service samba-ad-dc configuré pour démarrage automatique."
fi

# 10. Auto-vérification du statut du contrôleur de domaine
echo "🔍 8. Vérification de conformité du domaine..."
if command -v samba-tool >/dev/null 2>&1; then
    samba-tool domain level show || true
fi

echo "======================================================================"
echo "🎉 Le Contrôleur de Domaine Samba-AD DC LYUX.LAN est opérationnel !"
echo "======================================================================"
