# Catalogue logiciels — détection de versions et ajout réel

Note de conception : **non implémentée**. Elle complète l'ADR-019
(`.antigravity/memory/decisions.md`) sans la modifier. Le prototype React reste visuel
et n'effectue aucun appel réseau.

## 1. Ce que fait le prototype aujourd'hui

La page `/logiciels/` permet de saisir un nom, un lien, une source, une version, une
catégorie, un public cible et des arguments de lancement. Les catégories du catalogue
incluent Proton et Wine ; la liste des logiciels prévus suit la [matrice de compatibilité du
wiki `lyux-desktop`](https://github.com/Luux-Manchot/lyux-desktop/wiki/Logiciels-et-compatibilite).
Le bouton « Vérifier » renvoie une version
simulée et « Ajouter au catalogue » crée une fiche visible dans la session. Tout disparaît
au rechargement : aucun artefact n'est téléchargé, aucune version n'est réellement détectée,
aucun logiciel n'est installé sur les postes.

## 2. Pourquoi la détection réelle ne peut pas se faire dans le navigateur

- Les sites externes refusent généralement les appels directs depuis une autre origine (CORS).
- Un lien saisi par un administrateur n'est pas une source fiable : il peut être détourné
  ou servir un artefact différent d'une version à l'autre.
- Le navigateur n'a aucun droit pour installer un paquet sur les postes du lycée.
- La page admin est servie par `lyux-hub` ; lui faire interroger des URL arbitraires
  ouvrirait une surface de requêtes internes indésirables (SSRF).

La détection et l'ajout réel doivent donc être réalisés côté serveur ; seuls les
résultats validés sont ensuite affichés dans le panneau.

## 3. Architecture envisagée

1. **Liste blanche de sources** : pour chaque logiciel, une URL et un type de source
   (`site officiel`, `GitHub releases`, `Flathub`, `dépôt Debian`, `Fastpack`). Aucune URL
   libre n'est acceptée depuis l'interface.
2. **Collecteur dans `lyux-api`** : interroge les sources autorisées, avec un cache et un
   délai d'expiration. En cas d'absence de réseau, le dernier résultat connu est conservé.
3. **Normalisation** : extraction de la dernière version (numéro, date de publication,
   empreinte annoncée) et comparaison avec la version du registre.
4. **Vérification** : téléchargement de l'artefact dans `/srv/lyux/releases`, calcul des
   empreintes SHA-256 et vérification de la signature détachée Ed25519. Un artefact non
   signé ou dont l'empreinte diffère est refusé avant toute publication.
5. **Registre et manifeste** : création d'une entrée de version avec son manifeste signé,
   puis publication sur le canal voulu uniquement après validation administrative.
6. **Distribution** : `lyux-api` sert les artefacts derrière `lyux-hub` (`lyux-api:8000`
   non exposé directement). Le client LyuX vérifie le manifeste avant d'appliquer la mise
   à jour ; la version précédente est conservée pour un retour arrière.

Le cache APT du port 3142 accélère les téléchargements mais **n'est pas un dépôt signé** :
il ne remplace ni la vérification d'empreinte ni la signature.

## 4. Points à trancher avant implémentation

Les quatre questions déjà ouvertes dans l'ADR-019 restent bloquantes :

1. Quel est le format exact de Fastpack : `.deb`, AppImage, Flatpak ou binaire maison ?
2. Mettre à jour l'OS signifie-t-il un simple `apt` sur Debian Trixie, ou le remplacement
   d'une image complète ?
3. Le serveur a-t-il accès à Internet, ou faut-il prévoir un fonctionnement LAN uniquement ?
4. Les mises à jour sont-elles automatiques ou validées manuellement par l'administrateur ?

À ces questions s'ajoutent, pour le catalogue logiciels :

- quelles sources autoriser et qui les maintient ;
- si un logiciel absent de la liste blanche peut être ajouté manuellement, et avec quels
  contrôles ;
- qui valide la publication d'une nouvelle version détectée.

## 5. Sécurité et exploitation

- Aucune URL arbitraire depuis le navigateur : seulement des identifiants de sources
  connues du serveur.
- Écritures protégées par authentification administrateur et journalisées.
- Artefacts signés uniquement ; aucune exécution d'installateur non vérifié.
- Arguments de lancement stockés comme liste de chaînes validées, jamais interprétés par un
  shell, et couverts par le manifeste signé.
- Détection, distribution et application restent trois étapes distinctes (ADR-019).
- Fonctionnement dégradé prévu si Internet est indisponible : versions connues conservées,
  aucune mise à jour proposée tant que la vérification n'est pas possible.

## 6. Suivi

Cette piste concerne l'ADR-019 (`lyux-server#14`), le socle API (`#16`) et les pages
d'administration (`#15`). Elle consomme les besoins déjà décrits dans les issues `#9`,
`#11`, `#12` et `#13` sans les dupliquer. Aucun changement de ce document n'implique une
modification de `docker-compose.yml` ou de Cockpit natif.
