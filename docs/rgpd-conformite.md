# 📜 Conformité RGPD & Cadre Légal

Le déploiement d'une infrastructure informatique dans un établissement scolaire accueillant des mineurs impose le strict respect de la réglementation française et européenne (**RGPD**, loi pour la confiance dans l'économie numérique, circulaire de l'Éducation Nationale).

---

## 1. Obligations Légales de Journalisation

* **Rétention des logs de connexion et de navigation** : Conservation obligatoire des traces techniques pendant **1 an** (Loi n° 2006-64 du 23 janvier 2006 relative à la lutte contre le terrorisme).
* **Données journalisées** :
  * Date, heure et adresse IP du poste client.
  * Identifiant du compte utilisateur connecté.
  * URL et adresses IP des sites internet visités (via le proxy Squid / e2guardian).
* **Accès restreint** : Les journaux ne peuvent être consultés que par le chef d'établissement, les administrateurs habilités ou sur réquisition judiciaire.

---

## 2. Principes RGPD Appliqués dans LyuX

1. **Minimisation des Données** :
   * Les comptes utilisateurs ne contiennent que les attributs strictement nécessaires (Nom, Prénom, Classe, Identifiant).
   * Aucune donnée biométrique ou bancaire n'est stockée sur l'infrastructure LyuX.
2. **Droit à l'Oubli & Cycle de Vie** :
   * À la fin de chaque année scolaire, les comptes des élèves ayant quitté l'établissement sont archivés puis supprimés (délai de grâce de 3 mois pour récupération des travaux).
3. **Sécurité & Chiffrement** :
   * Tous les flux d'administration et d'accès web sont chiffrés en **HTTPS / TLS**.
   * Les sauvegardes 3-2-1 hors-site sont systématiquement chiffrées avec des clés fortes.
4. **Charte Informatique de l'Établissement** :
   * Annexée au règlement intérieur du lycée, signée par chaque élève et ses responsables légaux en début d'année.
