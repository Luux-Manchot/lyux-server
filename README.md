# 🖧 LyuX Server (`lyux-server`)

Services centraux, annuaire, stockage et API de gestion pour le déploiement du réseau **LyuX (Opération Manchot)** en établissement scolaire.

## 📦 Composants inclus

- **`lyux-server-api`** : API REST FastAPI (enrôlement OTP, salles/machines, télémétrie, diagnostic). Déjà conteneurisée (`lyux-api`, port 8000).
- **`apps/cockpit`** : 4 plugins d'administration LyuX (`lyux`, `parc`, `discover`, `users`), source unique installable dans Cockpit.
- **`apps/hub`** : conteneur nginx `lyux-hub` qui sert ces plugins de façon autonome (port 8086) et proxie `/api` vers `lyux-api`. Voir [`docs/admin-panel-docker.md`](docs/admin-panel-docker.md).
- **`apps/admin-ui`** : prototype visuel React/Vite du futur panneau d'administration, avec données simulées et sans connexion à l'API ni à Docker. Voir [`apps/admin-ui/README.md`](apps/admin-ui/README.md).
- **`lyux-server-infra`** : stack Docker (Traefik, Apt-Cacher-NG, GLPI + MariaDB, LAM, Uptime Kuma, `lyux-api`, `lyux-hub`) et scripts système.
- **`docs/`** : architecture, RGPD et notes d'administration.
- **`tests/`** : tests pytest du domaine serveur.

> Cockpit lui-même reste **natif** sur le port 9090 (socket systemd) pour l'administration système : le conteneuriser exigerait `--privileged`, D-Bus hôte et l'accès à `/etc/shadow`. Samba-AD, les partages et UFW sont également gérés côté hôte par les scripts de `lyux-server-infra/scripts/`.

## 🚀 Démarrage rapide

```bash
# API seule (développement)
python -m uvicorn --app-dir lyux-server-api/src main:app --port 8000 --host 0.0.0.0

# Stack complète (production / lab)
cd lyux-server-infra
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Admin panel conteneurisé : `http://<ip-serveur>:8086/` (ou `http://hub.lyux.lan/` via Traefik).
Administration système : `https://<ip-serveur>:9090/`.
