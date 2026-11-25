#!/usr/bin/env bash
# ==============================================================================
# Script d'initialisation du Serveur Central LyuX (Debian 12 / Ubuntu 24.04)
# ==============================================================================
set -euo pipefail

echo "======================================================="
echo "🐧 Initialisation du Serveur Central LyuX (Opération Manchot)"
echo "======================================================="

# Vérification des privilèges root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Ce script doit être exécuté en tant que root (sudo)."
  exit 1
fi

# 1. Mise à jour de l'OS
echo "📦 1. Mise à jour des paquets système..."
apt update && apt upgrade -y

# 2. Installation des paquets essentiels
echo "📦 2. Installation des paquets prérequis..."
apt install -y \
    curl \
    wget \
    git \
    cockpit \
    cockpit-storaged \
    cockpit-networkmanager \
    cockpit-packagekit \
    samba \
    samba-common-bin \
    acl \
    quota \
    slapd \
    ldap-utils \
    libnss-ldapd \
    libpam-ldapd \
    nfs-kernel-server \
    ufw \
    rsync \
    jq \
    python3 \
    python3-pip \
    python3-ldap \
    dnsmasq

# 3. Création des arborescences de stockage partagé
echo "📁 3. Création des dossiers de stockage réseau..."
mkdir -p /srv/samba/{homes,classes,profs,administration,commun}
mkdir -p /srv/backups/daily
chmod 755 /srv/samba
chmod 775 /srv/samba/commun
chmod 770 /srv/samba/{classes,profs,administration}

# 4. Création des groupes système standards
echo "👥 4. Création des groupes d'utilisateurs..."
getent group eleves >/dev/null || groupadd -g 2000 eleves
getent group enseignants >/dev/null || groupadd -g 2001 enseignants
getent group administration >/dev/null || groupadd -g 2002 administration
getent group viesco >/dev/null || groupadd -g 2003 viesco
getent group techniciens >/dev/null || groupadd -g 2004 techniciens

# 5. Création du helper de création de home dynamique
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
fi
EOF
chmod +x /usr/local/bin/lyux-create-user-home.sh

# 6. Configuration du Pare-feu UFW
echo "🛡️ 6. Configuration du pare-feu..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP Traefik'
ufw allow 443/tcp comment 'HTTPS Traefik'
ufw allow 8080/tcp comment 'Traefik Dashboard'
ufw allow 3142/tcp comment 'Apt-Cacher-NG'
ufw allow 139/tcp comment 'Samba NetBIOS'
ufw allow 445/tcp comment 'Samba SMB'
ufw allow 389/tcp comment 'LDAP'
ufw allow 636/tcp comment 'LDAPS'
ufw allow 3001/tcp comment 'Supervision Uptime Kuma'
ufw allow 8087/tcp comment 'LyuX Admin UI'
ufw allow 8082/tcp comment 'LAM Web'
ufw allow 8085/tcp comment 'GLPI Web'
ufw allow 8000/tcp comment 'LyuX Control API'
ufw --force enable

# 6b. DHCP + DNS du réseau pédagogique interne (les clients récupèrent une IP
#     et « serveur.lyux.lan » sans aucune configuration locale figée).
echo "🌐 6b. DHCP/DNS du lab (dnsmasq)..."
LAB_IF="${LYUX_LAB_IF:-enp0s3}"
LAB_IP="${LYUX_LAB_IP:-192.168.10.1}"
LAB_NET="${LYUX_LAB_NET:-192.168.10.0}"
LAB_MASK="${LYUX_LAB_MASK:-255.255.255.0}"
LAB_POOL_START="${LYUX_LAB_POOL_START:-192.168.10.100}"
LAB_POOL_END="${LYUX_LAB_POOL_END:-192.168.10.200}"

# Debian 13 commente conf-dir par défaut : on l'active pour charger notre fichier.
if grep -q '^#conf-dir=/etc/dnsmasq.d' /etc/dnsmasq.conf; then
    sed -i 's|^#conf-dir=/etc/dnsmasq.d,*.conf|conf-dir=/etc/dnsmasq.d,*.conf|' /etc/dnsmasq.conf
fi

cat << EOF > /etc/dnsmasq.d/lyux-lab.conf
# Réseau pédagogique LyuX — généré par init-server.sh
interface=${LAB_IF}
bind-interfaces
domain=lyux.lan
dhcp-range=${LAB_POOL_START},${LAB_POOL_END},${LAB_MASK},12h
dhcp-option=3,${LAB_IP}
dhcp-option=6,${LAB_IP}
address=/serveur.lyux.lan/${LAB_IP}
address=/server.lyux.lan/${LAB_IP}
EOF

# Le service doit répondre au DHCP (67/udp) et au DNS (53) sur l'interface du lab.
ufw allow in on "${LAB_IF}" proto udp port 67 comment 'DHCP lab'
ufw allow out on "${LAB_IF}" proto udp port 68 comment 'DHCP lab'
ufw allow in on "${LAB_IF}" proto udp port 53 comment 'DNS lab'
ufw allow in on "${LAB_IF}" proto tcp port 53 comment 'DNS lab'

systemctl enable --now dnsmasq

# 7. Désactivation de l'ancien port 9090 (Cockpit remplacé par LyuX Admin UI sur 8087)
echo "🎛️ 7. Désactivation de l'ancien service Cockpit (remplacé par admin.lyux.lan:8087)..."
if command -v systemctl >/dev/null 2>&1; then
    systemctl disable --now cockpit.socket 2>/dev/null || true
    ufw delete allow 9090/tcp 2>/dev/null || true
fi

# 8. Initialisation automatisée des sondes Uptime Kuma
echo "📡 8. Initialisation des sondes de supervision Uptime Kuma..."
KUMA_SCRIPT="${SCRIPT_DIR}/init-kuma-monitors.py"
if [ -f "${KUMA_SCRIPT}" ] && command -v python3 >/dev/null 2>&1; then
    python3 "${KUMA_SCRIPT}" || echo "ℹ️ Provisioning Uptime Kuma différé (la base sera initialisée au premier lancement du conteneur)."
fi

# 9. Configuration du stockage partagé, des ACLs POSIX et des quotas
echo "📁 9. Configuration du stockage partagé, des ACLs et des quotas..."
SHARES_SCRIPT="${SCRIPT_DIR}/setup-shares.sh"
if [ -f "${SHARES_SCRIPT}" ]; then
    bash "${SHARES_SCRIPT}" || echo "⚠️ Erreur non bloquante lors de setup-shares.sh"
fi

# 10. Provisioning du Contrôleur de Domaine Samba-AD DC
echo "🏰 10. Provisioning du domaine Samba-AD DC..."
SAMBA_AD_SCRIPT="${SCRIPT_DIR}/setup-samba-ad.sh"
if [ -f "${SAMBA_AD_SCRIPT}" ]; then
    bash "${SAMBA_AD_SCRIPT}" || echo "⚠️ Erreur non bloquante lors de setup-samba-ad.sh"
fi

# 11. Importation et provisionnement des comptes utilisateurs de test
echo "👥 11. Importation des comptes de test via import-users-csv.py..."
IMPORT_SCRIPT="${SCRIPT_DIR}/import-users-csv.py"
CSV_FILE="${SCRIPT_DIR}/../configs/utilisateurs-test.csv"
if [ -f "${IMPORT_SCRIPT}" ] && [ -f "${CSV_FILE}" ] && command -v python3 >/dev/null 2>&1; then
    python3 "${IMPORT_SCRIPT}" "${CSV_FILE}" || echo "⚠️ Erreur non bloquante lors de import-users-csv.py"
fi

# 12. Démarrage de la stack Docker Compose et configuration LAM
echo "🐳 12. Démarrage des conteneurs d'infrastructure..."
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    (cd "${SCRIPT_DIR}/.." && docker compose up -d) || echo "⚠️ Avertissement lors du lancement de docker compose"
fi

echo "🐧 13. Configuration et vérification du profil LDAP Account Manager (LAM)..."
LAM_SCRIPT="${SCRIPT_DIR}/setup-lam.sh"
if [ -f "${LAM_SCRIPT}" ]; then
    bash "${LAM_SCRIPT}" || echo "⚠️ Erreur non bloquante lors de setup-lam.sh"
fi

echo "✅ Initialisation système terminée."
