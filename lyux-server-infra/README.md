# 🏛️ LyuX Server Infra
> **Stack d'infrastructure centrale pour l'établissement scolaire (Docker & Services Système).**

Ce sous-projet regroupe la configuration du serveur central de l'établissement. Il combine une pile **Docker Compose** pour les services d'administration, de gestion de parc et de supervision, ainsi que les configurations système pour l'annuaire d'utilisateurs et le partage de fichiers.

---

## 📋 Services Embarqués

| Service | Rôle | Port Interne / URL |
| :--- | :--- | :--- |
| **Cockpit** | Administration système web, stockage & réseau | `https://server.lyux.lan:9090` (Port `9090`) |
| **Traefik** | Reverse Proxy HTTP/HTTPS & routage local | `80`, `443`, Dashboard: `8080` |
| **GLPI + MariaDB** | Inventaire de parc & Système de tickets d'assistance | `http://glpi.lyux.lan` ou Port direct `8085` |
| **Apt-Cacher-NG** | Serveur de cache local pour les paquets `.deb` (Debian/Ubuntu) | Port `3142` |
| **LDAP Account Manager (LAM)** | Gestion web des utilisateurs, groupes et réinitialisation de mots de passe | `http://lam.lyux.lan` ou Port direct `8082` |
| **Self-Service Password** | Portail web permettant aux élèves de changer leur mot de passe | `http://mdp.lyux.lan` |
| **Uptime Kuma** | Supervision simple et alertes sur l'état des serveurs et du réseau | `http://supervision.lyux.lan:3001` (Port `3001`) |
| **LyuX Control API** | API REST pour la validation des enrôlements de machines et profils Ansible | `http://api.lyux.lan:8000` (Port `8000`) |
| **Samba File Server** | Partages CIFS des dossiers personnels (`/home`) et dossiers de classes | Ports `139`, `445` |

---

## ⚙️ Prérequis

- **Système d'exploitation recommandé** : Debian 12 (Bookworm) ou Ubuntu Server 24.04 LTS.
- **Docker Engine & Docker Compose Plugin** (`docker compose version` >= 2.20).
- **Ressources recommandées** : 4 à 8 cœurs CPU, 16 Go de RAM, stockage SSD/NVMe (avec RAID ou ZFS).

---

## 🚀 Déploiement

1. **Cloner ou se placer dans le répertoire** :
   ```bash
   cd projects/lyux-server-infra
   ```

2. **Créer le fichier d'environnement** :
   ```bash
   cp .env.example .env
   # Éditez .env pour définir vos mots de passe sécurisés et le domaine de l'établissement
   nano .env
   ```

3. **Lancer les conteneurs** :
   ```bash
   docker compose up -d
   ```

4. **Vérifier l'état des conteneurs** :
   ```bash
   docker compose ps
   ```

---

## 📂 Organisation des Dossiers

```
lyux-server-infra/
├── docker-compose.yml          # Définition de tous les conteneurs Docker
├── .env.example                # Variables d'environnement type
├── configs/
│   ├── apt-cacher-ng/          # Configuration du cache APT
│   ├── cockpit/                # Configuration Cockpit (cockpit.conf, issue.cockpit)
│   ├── traefik/                # Configuration dynamique et statique Traefik
│   ├── samba/                  # Modèle smb.conf pour les partages classes/homes
│   └── lam/                    # Profils pour LDAP Account Manager
├── scripts/
│   ├── init-server.sh          # Script d'initialisation post-installation de l'OS
│   ├── init-kuma-monitors.py   # Initialisation automatisée des sondes Uptime Kuma
│   ├── import-users-csv.py     # Script d'import CSV (élèves/profs) vers l'annuaire
│   └── backup-321.sh           # Sauvegarde chiffrée automatique quotidienne
└── docs/                       # Guides d'administration et de maintenance
```

---

## 🔒 Sauvegardes & Stratégie 3-2-1
Le script [`scripts/backup-321.sh`](file:///g:/Pro/.Dev/Lycee/Op%C3%A9rationManchot/projects/lyux-server-infra/scripts/backup-321.sh) automatise :
1. Le dump de la base MariaDB de GLPI.
2. La sauvegarde de l'annuaire LDAP (fichiers LDIF).
3. La sauvegarde des répertoires de configuration `/etc` et Docker.
4. L'export incrémental chiffré vers un NAS de sauvegarde local et un dépôt hors-site.
