# Architecture de Distribution des Logiciels & Store LyuX

Ce document explique le fonctionnement du **Store d'applications** (`http://<serveur>:8087/logiciels/`) et du déploiement optimisé sur les postes clients universels.

---

## 1. Catalogue "Store" (style KDE Discover)
- **Sources en direct** (`GET /api/v1/apps/store/search`) :
  1. **Flathub (`https://flathub.org/api/v2`)** : recherche en temps réel de milliers d'applications Linux (icône, description, catégorie, `flatpak_id`).
  2. **Dépôt Debian APT (`apt-cache search`)** : recherche dans les paquets `.deb` officiels de Debian 13.
  3. **Fallback hors-ligne** : si le serveur n'a pas accès à Internet, une liste curée intégrée reste disponible.
- **Ajout & droits par rôle** : lors de l'ajout (ou sur la fiche d'une appli existante), l'administrateur choisit les **rôles autorisés** (`eleve`, `prof`, `viesco`, `administration`, `admin`).

---

## 2. Téléchargement optimisé sur les postes clients (Cache LAN / Pair + Fallback Internet)
Chaque poste client exécute périodiquement `sync_client_packages()` (via le timer `lyux-nss-sync.timer` toutes les 5 minutes) en interrogeant `GET /api/v1/apps/client` :

1. **Priorité au cache LAN le plus rapide (`_pick_fastest_cache_proxy`)** :
   - Le serveur fournit `cache_proxy` (`apt-cacher-ng` sur le port `3142`) et `peer_caches` (les postes pairs en ligne disposant d'un relais/cache sur le port `3142`).
   - Le client mesure la latence TCP vers chacun et utilise le cache LAN le plus rapide : le premier poste qui télécharge un paquet `.deb` le met en cache, et tous les autres postes de la salle le récupèrent ensuite en local à **1 Gbps** sans saturer la connexion Internet du lycée.
2. **Bascule automatique sur Internet (`fallback_direct: true`)** :
   - Si aucun cache serveur/pair n'est joignable, ou si l'installation via le proxy échoue, le client **bascule automatiquement en téléchargement direct sur Internet** (`Acquire::http::Proxy=false` pour APT, et Flathub direct pour les Flatpaks) afin que l'installation aboutisse dans tous les cas.

---

## 3. Contrôle d'exécution par rôle sur PC universels
- Tous les logiciels déployés sont installés sur le disque des postes (indépendamment de qui est assis devant).
- À chaque ouverture de session (`pam_session_hook.py` → `apply_role_app_restrictions()`), le client récupère `/api/v1/apps/client?role=<role_utilisateur>` et masque (`NoDisplay=true` / `Hidden=true` dans `~/.local/share/applications/`) les lanceurs des applications non autorisées pour le rôle de l'utilisateur connecté (et les rétablit s'il est autorisé).
