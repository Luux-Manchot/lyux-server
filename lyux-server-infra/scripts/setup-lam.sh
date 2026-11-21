#!/usr/bin/env bash
# ==============================================================================
# Script de Déploiement du Profil LDAP Account Manager (LAM) LyuX
# Emplacement cible : projects/lyux-server-infra/scripts/setup-lam.sh
# ==============================================================================
set -euo pipefail

echo "======================================================================"
echo "🐧 Déploiement et Configuration de LDAP Account Manager (LAM)"
echo "======================================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../configs/lam"
COMPOSE_DIR="${SCRIPT_DIR}/.."

# 1. Vérification des fichiers sources
if [ ! -f "${CONFIG_DIR}/config.cfg" ] || [ ! -f "${CONFIG_DIR}/lyux.conf" ]; then
    echo "❌ Fichiers config.cfg ou lyux.conf introuvables dans ${CONFIG_DIR}."
    exit 1
fi

echo "📋 1. Fichiers de configuration LAM détectés avec succès :"
ls -la "${CONFIG_DIR}"

# 2. Vérification et injection dans le volume persistant Docker lam_data
# Emplacement type sous Docker Linux : /var/lib/docker/volumes/... ou via docker cp
CONTAINER_NAME="lyux-lam"

if command -v docker >/dev/null 2>&1 && docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🐳 2. Injection des configurations dans le conteneur ${CONTAINER_NAME}..."
    docker exec "${CONTAINER_NAME}" mkdir -p /var/lib/ldap-account-manager/config/profiles
    docker cp "${CONFIG_DIR}/config.cfg" "${CONTAINER_NAME}:/var/lib/ldap-account-manager/config/config.cfg"
    docker cp "${CONFIG_DIR}/lyux.conf" "${CONTAINER_NAME}:/var/lib/ldap-account-manager/config/profiles/lyux.conf"
    
    # Ajustement des permissions au propriétaire web (www-data / 33:33)
    docker exec "${CONTAINER_NAME}" chown -R 33:33 /var/lib/ldap-account-manager/config
    docker exec "${CONTAINER_NAME}" chmod 644 /var/lib/ldap-account-manager/config/config.cfg
    docker exec "${CONTAINER_NAME}" chmod 644 /var/lib/ldap-account-manager/config/profiles/lyux.conf

    echo "🔄 3. Redémarrage du conteneur ${CONTAINER_NAME}..."
    docker restart "${CONTAINER_NAME}"
    echo "✅ Profil LyuX appliqué et conteneur redémarré."
else
    echo "ℹ️ Le conteneur ${CONTAINER_NAME} n'est pas encore en cours d'exécution."
    echo "👉 Les fichiers sont prêts dans ${CONFIG_DIR} et seront montés/copiés au démarrage du conteneur."
fi

# 3. Test de connectivité HTTP sur le port direct 8082
LAM_PORT="${LAM_HTTP_PORT:-8082}"
echo "🌐 4. Vérification de l'accès au service LAM (Port ${LAM_PORT})..."
if command -v curl >/dev/null 2>&1; then
    if curl -s -f -o /dev/null "http://localhost:${LAM_PORT}/" 2>/dev/null; then
        echo "✅ LAM répond favorablement sur http://localhost:${LAM_PORT}/"
    else
        echo "ℹ️ LAM sera accessible dès le démarrage de la pile Docker Compose (docker compose up -d)."
    fi
fi

echo "======================================================================"
echo "🎉 Déploiement du profil LAM LyuX achevé avec succès !"
echo "======================================================================"
