# 🏛️ LyuX Server Infra
> **Stack d'infrastructure centrale pour l'établissement scolaire (Docker & services système).**

Ce sous-projet regroupe la configuration du serveur central. Il combine une pile **Docker Compose** pour les services d'administration, de gestion de parc et de supervision, ainsi que les configurations système pour l'annuaire et le partage de fichiers.

---

## 📋 Services embarqués

| Service | Rôle | Port / URL |
| :--- | :--- | :--- |
| **Cockpit** (natif) | Administration système web, stockage & réseau | `https://server.lyux.lan:9090` |
| **lyux-hub** | Admin panel LyuX conteneurisé (plugins Cockpit servis seuls) | `http://hub.lyux.lan` ou `:8086` |
| **Traefik** | Reverse proxy HTTP & routage local | `8088`, dashboard `8888` |
| **GLPI + MariaDB** | Inventaire de parc & tickets d'assistance | `http://glpi.lyux.lan` ou `:8085` |
| **Apt-Cacher-NG** | Cache local des paquets `.deb` | `:3142` |
| **LDAP Account Manager (LAM)** | Gestion des comptes et groupes LDAP | `http://lam.lyux.lan` ou `:8082` |
| **Uptime Kuma** | Supervision et alertes | `http://supervision.lyux.lan:3001` |
| **LyuX Control API** | Enrôlement, salles/machines, télémétrie | `http://api.lyux.lan:8000` |
| **Samba / partages** (natif) | CIFS `/homes` et `/classes` | `139`, `445` |

> Samba-AD, les partages, UFW et Cockpit sont gérés sur l'hôte par `scripts/init-server.sh` et les scripts associés. Voir aussi [`../docs/admin-panel-docker.md`](../docs/admin-panel-docker.md).

---

## ⚙️ Prérequis

- Debian 12 (Bookworm) ou Ubuntu Server 24.04 LTS.
- Docker Engine & Docker Compose Plugin (`docker compose version` >= 2.20).
- 4 à 8 cœurs CPU, 16 Go de RAM, stockage SSD/NVMe.

---

## 🚀 Déploiement

```bash
cd lyux-server-infra
cp .env.example .env       # renseigner les mots de passe de l'établissement
nano .env
docker compose up -d --build
docker compose ps
```

---

## 📂 Organisation des dossiers

```
lyux-server/
├── apps/
│   ├── cockpit/            # Plugins Cockpit (lyux, parc, discover, users)
│   └── hub/                # Dockerfile + nginx du conteneur lyux-hub
├── lyux-server-api/        # API FastAPI (lyux-api)
├── lyux-server-infra/
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── configs/
│   │   ├── apt-cacher-ng/
│   │   ├── cockpit/
│   │   ├── traefik/
│   │   ├── samba/
│   │   └── lam/
│   └── scripts/
│       ├── init-server.sh
│       ├── init-kuma-monitors.py
│       ├── import-users-csv.py
│       ├── backup-321.sh
│       ├── fix-ownership.sh
│       ├── init-user-folders.sh
│       ├── set-passwords.sh
│       └── setup-nfs-export.sh
├── docs/
├── tests/
└── README.md
```

---

## 🔒 Sauvegardes & stratégie 3-2-1

Le script [`scripts/backup-321.sh`](scripts/backup-321.sh) automatise :

1. Le dump de la base MariaDB de GLPI.
2. La sauvegarde de l'annuaire LDAP (fichiers LDIF).
3. La sauvegarde des répertoires de configuration `/etc` et Docker.
4. L'export incrémental chiffré vers un NAS local et un dépôt hors-site.
