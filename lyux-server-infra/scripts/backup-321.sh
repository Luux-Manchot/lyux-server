#!/usr/bin/env bash
# ==============================================================================
# Script de sauvegarde automatique 3-2-1 pour serveur LyuX
# Règle 3-2-1 : 3 copies, 2 supports différents, 1 hors-site
# ==============================================================================
set -euo pipefail

BACKUP_DIR="/srv/backups/daily"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
TARGET_FILE="$BACKUP_DIR/lyux_backup_$DATE.tar.gz"

echo "💾 Démarrage de la sauvegarde quotidienne LyuX ($DATE)..."
mkdir -p "$BACKUP_DIR"

# 1. Sauvegarde de la base MariaDB GLPI
echo "📦 Dump de la base GLPI..."
docker exec lyux-glpi-db mariadb-dump -u root -p"${GLPI_DB_ROOT_PASSWORD:-root_secret_pass}" --all-databases > /tmp/glpi_dump.sql

# 2. Sauvegarde de la configuration Samba et configurations système
echo "📦 Archivage des configurations et bases de données..."
tar -czf "$TARGET_FILE" \
    /etc/samba \
    /etc/ldap \
    /tmp/glpi_dump.sql \
    /srv/samba/administration \
    /srv/samba/profs

# Nettoyage fichier temporaire
rm -f /tmp/glpi_dump.sql

# 3. Rétention locale : conserver les 7 derniers jours
echo "🧹 Nettoyage des anciennes sauvegardes locales (> 7 jours)..."
find "$BACKUP_DIR" -type f -name "lyux_backup_*.tar.gz" -mtime +7 -delete

echo "✅ Sauvegarde locale réussie : $TARGET_FILE"
echo "👉 Prêt pour synchronisation rsync / Restic vers le NAS distant ou serveur hors-site."
