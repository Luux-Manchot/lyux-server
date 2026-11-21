# 🌐 LyuX Control API & Server Plane
> **API REST centrale d'orchestration, de validation d'enrôlement et de gestion de profils (FastAPI).**

Ce microservice backend agit comme le cerveau central de communication entre les postes clients (assistant d'enrôlement, widget de tickets) et l'infrastructure de l'établissement (GLPI, Ansible, Annuaire).

---

## 🚀 Fonctionnalités & Endpoints

1. **Gestion des Enrôlements & Codes OTP** :
   * `POST /api/v1/enroll/generate-otp` : Génère un code d'enrôlement à usage unique (valable 15 minutes) pour les techniciens déployant une salle.
   * `POST /api/v1/enroll/validate-otp` : Valide le code, enregistre le matériel dans GLPI et renvoie les variables de configuration Ansible pour la machine.
2. **Référentiel des Salles & Profils** :
   * `GET /api/v1/rooms` : Liste des salles de l'établissement et des profils logiciels associés (`nsi`, `sciences`, `techno`, `standard`).
3. **Passerelle Tickets d'Incidents** :
   * `POST /api/v1/tickets` : Reçoit les signalements provenant de l'application `lyux-report` et les insère automatiquement dans GLPI.

---

## 💻 Démarrage Local

```bash
cd projects/lyux-server-api
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Documentation interactive Swagger disponible sur : `http://localhost:8000/docs`

---

## 📂 Structure

```
lyux-server-api/
├── Dockerfile                  # Image conteneurisée pour docker-compose
├── requirements.txt            # Dépendances (FastAPI, Uvicorn, Pydantic)
├── src/
│   ├── main.py                 # Points d'entrée de l'API
│   ├── models.py               # Schémas de validation Pydantic
│   └── config.py               # Paramètres & variables d'environnement
└── README.md
```
