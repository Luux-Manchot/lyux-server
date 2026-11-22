# 🏛️ Architecture Technique Détaillée — Système LyuX

Ce document décrit en profondeur les flux de données, la sécurité, l'authentification et l'architecture réseau du projet **Opération Manchot (LyuX)**.

---

## 1. Schéma des Flux et Découpage Réseau

Pour garantir la sécurité et la séparation des usages dans un lycée, le réseau est segmenté en **VLANs** distincts :

```mermaid
graph TD
    subgraph ROUTEUR ["Pare-feu / Routeur d'Établissement"]
        FW["Filtrage & Routage Inter-VLAN"]
    end

    subgraph VLAN_SRV ["VLAN 10 : Serveurs (192.168.10.0/24)"]
        SRV_MAIN["Serveur LyuX (Docker, Samba, LDAP, GLPI)"]
    end

    subgraph VLAN_PROFS ["VLAN 20 : Salle des Profs & Postes Enseignants (192.168.20.0/24)"]
        PC_PROF["PC Enseignants (Veyon Master)"]
    end

    subgraph VLAN_ELEVES ["VLAN 30 : Salles Pédagogiques & Élèves (192.168.30.0/24)"]
        PC_ELEVE["PC Élèves (Kiosk Verrouillé)"]
    end

    subgraph VLAN_ADMIN ["VLAN 40 : Administration & Direction (192.168.40.0/24)"]
        PC_ADMIN["Bureaux Administration (Postes Hybrides / Windows)"]
    end

    FW <--> VLAN_SRV
    FW <--> VLAN_PROFS
    FW <--> VLAN_ELEVES
    FW <--> VLAN_ADMIN
```

---

## 2. Cycle d'Authentification et Montage Réseau (`SSSD` + `pam_mount`)

Lorsqu'un utilisateur ouvre sa session sur n'importe quel poste du parc :

```mermaid
sequenceDiagram
    participant U as 👤 Utilisateur (Élève / Prof)
    participant SDDM as 🖥️ Écran de Connexion (SDDM)
    participant PAM as ⚙️ PAM / SSSD
    participant LDAP as 🏛️ Annuaire LDAP / Samba-AD
    participant CIFS as 📂 Serveur de Fichiers Samba
    participant XDG as 🎨 Session KDE Plasma

    U->>SDDM: Saisie login (prenom.nom) & mot de passe
    SDDM->>PAM: Demande d'authentification
    PAM->>LDAP: Vérification identifiants & Groupes
    LDAP-->>PAM: Validé (Groupes: eleves, classe_1g2)
    PAM->>CIFS: pam_mount : Montage transparent de //serveur/homes/login vers ~/Espace_Personnel
    PAM->>CIFS: pam_mount : Montage des partages de classe vers ~/Partages_Classes
    PAM-->>SDDM: Authentification réussie
    SDDM->>XDG: Démarrage KDE Plasma (Thème Kiosk)
    XDG->>U: Lancement automatique de lyux-welcome (au 1er login)
```

---

## 3. Verrouillage du Bureau : KDE Kiosk

Le système **KDE Kiosk** permet de figer l'environnement de bureau pour que chaque élève retrouve un poste propre et uniforme :
* **Barre des tâches fixe** : impossibilité de supprimer le menu ou les raccourcis essentiels.
* **Panneau de configuration restreint** : accès refusé aux réglages réseau, à la gestion des utilisateurs et aux services système.
* **Nettoyage automatique** : à la déconnexion ou à l'extinction, les fichiers temporaires locaux de `/tmp` et les caches applicatifs sont nettoyés pour préserver les performances du disque local.

---

## 4. Serveur Unique All-in-One & Postes Universels

L'infrastructure serveur et client LyuX est documentée dans le Wiki complet du projet :
* **[Architecture Serveur Unique](../wiki/Architecture-Serveur-Unique.md)** : Socle Debian 12 natif (Samba-AD, Partages, Cockpit) + Conteneurs Docker (MariaDB, GLPI, LAM, Uptime Kuma, Apt-Cacher, API Hub).
* **[Postes Universels & Rôles Dynamiques](../wiki/Postes-Universels-et-Roles-Dynamiques.md)** : Zéro distinction matérielle en salle. L'écran SDDM active le rôle Élève (Kiosk, 5 Go, Veyon Service) ou Enseignant (Supervision Veyon Master, 20 Go, gestion de classe).
* **[Stratégie de Test & Lab Virtuel SSH](../wiki/Strategie-de-Test-Lab-et-Automatisation-SSH.md)** : Déploiement en petites VMs pilotées à 100% en SSH et validées par la suite de tests automatisés.
