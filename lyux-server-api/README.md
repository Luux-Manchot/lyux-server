# 🌐 LyuX Control API & Server Plane
> **API REST centrale d'orchestration, de validation d'enrôlement et de gestion de parc (FastAPI).**

Backend de communication entre les postes clients (enrôlement, signalement, télémétrie) et l'infrastructure de l'établissement. Conteneurisé sous le nom `lyux-api` (port 8000) dans [`../lyux-server-infra/docker-compose.yml`](../lyux-server-infra/docker-compose.yml).

## 🚀 Fonctionnalités & endpoints (non exhaustif)

1. **Enrôlement & OTP**
   - `POST /api/v1/enroll/generate-otp`, `POST /api/v1/enroll/validate-otp`
   - `POST /api/v1/enroll/client-enroll`, `GET /api/v1/enroll/suggest-hostname`
   - `POST /api/v1/parc/enrollment-toggle` (`enrollment_enabled`, ADR-013)
2. **Salles, bâtiments et parc**
   - `GET/POST /api/v1/buildings`, `GET/POST /api/v1/rooms`, `GET /api/v1/machines`
3. **Classes & utilisateurs**
   - `GET /api/v1/classes`, `POST /api/v1/users/create`, `POST /api/v1/users/import-csv`
4. **Télémétrie, versions et applications**
   - `GET /api/v1/apps`, `POST /api/v1/apps/deploy`
   - `POST /api/v1/client/version-report`, `GET /api/v1/parc/fleet-versions`
5. **Intégrations**
   - `POST /api/v1/tickets` : pour l'instant **génère un identifiant local simulé**, sans appel GLPI.
   - `GET /api/v1/auth/sync` : lit `/etc/passwd`, `/etc/shadow` et `/etc/group` de l'hôte (à remplacer par LDAP avant exposition hors hôte).

> ⚠️ L'état applicatif est **en mémoire** : OTP, salles, machines, versions et paramètres sont perdus au redémarrage. Le volume Docker `api_data:/app/data` est monté mais encore inutilisé. Voir [`../docs/admin-panel-docker.md`](../docs/admin-panel-docker.md#reste-à-faire-avant-de-considérer-le-chantier-terminé).

## 💻 Démarrage local

```bash
cd lyux-server-api
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Documentation interactive : `http://localhost:8000/docs`

## 📂 Structure

```
lyux-server-api/
├── Dockerfile                  # Image utilisée par docker-compose
├── requirements.txt
├── src/
│   ├── main.py                 # API, redirections Hub, preseed, inventory
│   ├── models.py               # Schémas Pydantic
│   └── config.py               # Variables d'environnement
└── README.md
```
