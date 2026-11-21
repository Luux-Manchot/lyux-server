# 🎛️ Cockpit Web Administration — LyuX Server

Ce dossier contient les fichiers de configuration de **Cockpit Project**, la console web officielle et standardisée d'administration système du serveur central LyuX (Opération Manchot).

---

## 📌 Rôle & Fonctionnalités

Cockpit s'exécute nativement au niveau du système d'exploitation hôte (Debian 12 / Ubuntu 24.04 LTS) via un socket systemd léger (`cockpit.socket`). Il fournit une interface web sécurisée sur le port standard **9090/TCP** en **HTTPS** :

- **Surveillance des ressources** : Utilisation CPU, RAM, trafic réseau et charges I/O disque en temps réel.
- **Gestion du stockage (`cockpit-storaged`)** : Surveillance des disques physiques, volumes LVM/RAID, partages CIFS/NFS (`/srv/samba/{homes,classes}`) et santé S.M.A.R.T.
- **Gestion du réseau (`cockpit-networkmanager`)** : Configuration des interfaces réseau, VLANs, ponts et pare-feu.
- **Mises à jour logicielles (`cockpit-packagekit`)** : Détection et application des correctifs de sécurité de l'OS hôte.
- **Journaux système & terminaux** : Consultation des logs `systemd-journald` et terminal root/sudo web intégré.

---

## 📂 Fichiers de Configuration

| Fichier | Emplacement Système | Description |
| :--- | :--- | :--- |
| `cockpit.conf` | `/etc/cockpit/cockpit.conf` | Paramètres WebService (origines CORS autorisées, en-têtes proxy) et Session (timeout inactivité de 15 min, bannière). |
| `issue.cockpit` | `/etc/issue.cockpit` | Bannière d'avertissement institutionnelle affichée sur la page de connexion. |

---

## 🔐 Accès & Authentification

- **URL d'accès** : `https://server.lyux.lan:9090` ou `https://<ip-serveur>:9090`
- **Port** : `9090/TCP` (autorisé dans UFW via `init-server.sh`).
- **Authentification** : Authentification PAM standard de l'hôte (comptes `root` ou administrateurs avec privilèges `sudo`).
- **Certificats TLS** : Cockpit génère automatiquement un certificat TLS auto-signé dans `/etc/cockpit/ws-certs.d/` lors du premier lancement. Un certificat personnalisé (Let's Encrypt ou CA d'établissement) peut y être déposé.
