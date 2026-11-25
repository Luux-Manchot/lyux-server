# Admin panel LyuX : cockpit natif + Hub conteneurisé

## Décision retenue

Le **panneau d'administration reste Cockpit sur le port 9090** pour tout ce qui touche au système hôte (disques, réseau, services, firewall, logs). C'est un choix déjà documenté : `cockpit/ws` en conteneur demanderait D-Bus hôte, `/run/systemd`, `/etc/shadow`, `--privileged` et `--net=host`, ce qui casserait l'ADR-010 (Proxmox LXC / bare-metal / VM).

En revanche, les **interfaces légères LyuX** (les plugins « fait maison » autorisés par l'issue #8 et l'ADR-009) sont désormais servies par un conteneur **`lyux-hub`**. Elles restent aussi installables dans Cockpit : une seule source de fichiers dans `apps/cockpit/`.

```
Navigateur
  ├─ https://serveur:9090            -> Cockpit natif (système) + plugins LyuX optionnels
  └─ http://hub.lyux.lan (ou :8086)  -> lyux-hub (nginx) -> lyux-api:8000
```

## Contenu du dépôt

```
apps/
├─ cockpit/              # Source unique des 4 plugins (installables dans Cockpit)
│  ├─ lyux/              # Établissement / classes / utilisateurs
│  ├─ parc/              # Bâtiments, salles, machines, WOL
│  ├─ discover/          # Catalogue logiciel
│  └─ users/             # Module historique (incomplet)
└─ hub/                  # Conteneur du Hub autonome
   ├─ Dockerfile
   ├─ nginx.conf         # /api -> lyux-api, /docs -> OpenAPI
   ├─ base1/             # Shims cockpit.js / po.js / cockpit.css
   └─ www/index.html     # Page d'entrée
```

## Lancement

Depuis `lyux-server-infra/` :

```bash
cp .env.example .env      # HUB_HTTP_PORT=8086 par défaut
docker compose up -d --build lyux-hub
docker compose ps lyux-hub
```

Accès : `http://<ip-serveur>:8086/` ou `http://hub.lyux.lan/` derrière Traefik.

## Compatibilité des plugins

Chaque plugin calcule sa base API ainsi :

```js
const API_BASE = window.LYUX_API_BASE
    || (location.port === "9090" ? location.protocol + "//" + location.hostname + ":8000" : "");
```

- Dans `lyux-hub`, le shim `base1/cockpit.js` positionne `window.LYUX_API_BASE = "/api"` : les appels passent par le proxy nginx.
- Dans Cockpit natif, le vrai `cockpit.js` est utilisé et les appels vont directement sur le port 8000.

Le shim ne reproduit que `cockpit.location`, `cockpit.onlocationchanged` et un `cockpit.file().read()` vide : **le conteneur n'a pas accès au `/etc` de l'hôte**. Le plugin `cockpit-users` reste donc hérité et incomplet (`users.js`, `users.css`, `po.js` absents).

## Reste à faire avant de considérer le chantier terminé

1. **Persistance de l'API** : `lyux-server-api/src/main.py` stocke tout en mémoire (`ROOM_CATALOG`, `CLIENT_VERSIONS`, etc.). Le volume `api_data:/app/data` est monté mais inutilisé. Ajouter SQLite/Postgres avant les issues #11 et #13.
2. **Endpoint WOL** : `cockpit-parc` appelle `/api/v1/parc/wol`, l'issue #13 spécifie `POST /api/v1/control/wake`. Ni l'un ni l'autre n'existe côté API.
3. **Sécurité** : `/api/v1/auth/sync` lit `/etc/passwd`, `/etc/shadow` et `/etc/group`. À remplacer par LDAP/`samba-tool` avant d'exposer l'API hors de l'hôte.
4. **ADR-013** : `SYSTEM_SETTINGS` est défini deux fois dans `main.py` (lignes ~160 et ~1069) ; `enrollment_enabled` est écrasé au démarrage.
5. **ADR-011** : `cockpit-lyux` utilise encore Tailwind/Lucide/Google Fonts via CDN. À migrer vers les assets locaux de `cockpit-parc`.
