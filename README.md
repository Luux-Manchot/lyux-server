# 🖧 LyuX Server (`lyux-server`)

Services centraux, annuaire, stockage et API de gestion pour le déploiement du réseau **LyuX (Opération Manchot)** en établissement scolaire.

## 📦 Composants inclus
- **`lyux-server-api`** : API REST FastAPI (authentification, enrôlement OTP, inventaire des salles, diagnostic).
- **`lyux-server-infra`** : Infrastructure conteneurisée Docker :
  - Samba 4 Active Directory / OpenLDAP
  - Partages réseau SMB sécurisés par classe et casiers devoirs
  - Cockpit Web Admin (gestion du serveur)
  - LDAP Account Manager (LAM)
  - Uptime Kuma (supervision en temps réel des services)
  - Apt-Cacher-NG (cache local des dépôts Debian)

## 🚀 Démarrage de l'API
```bash
python -m uvicorn --app-dir lyux-server-api/src main:app --port 8000 --host 0.0.0.0
```
