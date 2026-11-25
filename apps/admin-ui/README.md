# LyuX Administration — prototype visuel

Prototype autonome du futur panneau d'administration LyuX, réalisé en React + Vite.
La couche visuelle est **le code frontend réel d'Open Admin** (`open-admin-org/open-admin`,
licence MIT) : feuille de style compilée, polices Open Sans / Font Awesome, classes
Bootstrap et conventions de balisage des vues Blade. Seules les données et la navigation
sont adaptées au contexte de l'établissement.

## Portée

- **Prototype visuel uniquement** : aucune requête HTTP vers l'API, aucune écriture.
- Les actions affichent une notification de simulation.
- La recherche de l'en-tête filtre le menu latéral (il n'y a plus de champ de recherche dans la sidebar) ; le bouton de notifications ouvre les événements récents simulés.
- Le profil « Alex Moreau » est affiché en bas de la sidebar, à la place de l'ancien bandeau « Mode prototype ». Un clic ouvre un menu avec l'action « Se déconnecter » (simulation).
- Les données sont définies dans `src/data/mock.js`.
- Le service n'est **pas** branché sur `docker-compose.yml` ni sur le Hub LyuX (`lyux-hub`).
- Le panneau Cockpit natif reste l'outil d'administration système de référence.
- L'ancienne page « Classes & logiciels » est séparée en deux pages distinctes : **Utilisateurs** (`/utilisateurs/`, comptes, classes et groupes de TP) et **Logiciels** (`/logiciels/`, catalogue applicatif). L'ancienne URL `/pedagogie/` redirige vers `/logiciels/`.
- Chaque domaine possède une vraie URL (`/dashboard/`, `/parc/`, `/pilotage/`, `/paquets/`, `/utilisateurs/`, `/logiciels/`, …) gérée par l'History API : les boutons précédent/suivant du navigateur fonctionnent.
- Les titres et sous-titres redondants des pages ont été supprimés : le fil d'Ariane de la barre supérieure identifie la page, et il ne reste qu'une barre d'actions en haut du contenu.
- Le groupe « Parc & salles » de la sidebar se déplie au clic : il liste un lien « Vue d'ensemble », une sous-page par bâtiment (`/parc/<slug>/`) et l'action « Ajouter un bâtiment ». La liste des bâtiments est partagée par l'application : un bâtiment ajouté apparaît immédiatement dans le menu, le tableau de bord et la page Parc.
- La page d'un bâtiment affiche ses salles sous forme de cartes, sans carte « État du bâtiment » ni tableau des postes. Chaque carte ouvre une sous-page de salle (`/parc/<bâtiment>/<salle>/`) avec les informations de la salle et les postes qui y sont rattachés. Le fil d'Ariane est affiché dans la barre supérieure, juste après le bouton menu, et suit la salle ouverte (précédent/suivant fonctionnels).
- Dans une salle, les postes sont sélectionnables (aucun bouton d'action dans une carte). Le panneau de droite affiche le poste choisi : dernière connexion, session utilisateur, disponibilité, mises à jour, IP, MAC, version client, build et bâtiment.
- Dans la page **Logiciels** (`/logiciels/`), la liste de gauche n'affiche que le nom des applications. La première est sélectionnée par défaut ; toute application peut être choisie et sa fiche complète s'affiche dans le panneau de droite.
- La page **Paquets & versions** (`/paquets/`) traduit visuellement l'ADR-019 : registre des versions, manifeste signé et politique de mise à jour. Elle est accessible depuis la sidebar et depuis un bouton de la page Pilotage.
- Le sens des couleurs (en ligne, hors ligne, mises à jour, alertes) est documenté dans [`../../docs/admin-ui-couleurs-etats.md`](../../docs/admin-ui-couleurs-etats.md).

## Réutilisation d'Open Admin

Aucun PHP n'est exécuté : seul le frontend est repris.

| Élément réutilisé | Origine | Emplacement dans le prototype |
| --- | --- | --- |
| Thème complet (Bootstrap 5.1.3 + Font Awesome + styles open-admin) | `resources/assets/open-admin/css/styles.css` | `src/vendor/open-admin/css/styles.css` |
| Styles du tableau de bord | `resources/assets/open-admin/css/pages/dashboard.css` | `src/vendor/open-admin/css/pages/dashboard.css` |
| Polices Open Sans | `resources/assets/open-admin/fonts/` | `src/vendor/open-admin/fonts/` |
| Polices Font Awesome | `resources/assets/fontawesome/webfonts/` | `src/vendor/fontawesome/webfonts/` |
| Avis de licence | `LICENSE`, `resources/assets/fontawesome/LICENSE.txt` | `src/vendor/open-admin/LICENSE-open-admin.txt`, `src/vendor/fontawesome/LICENSE-fontawesome.txt` |
| Balisage et classes | `resources/views/index.blade.php`, `content.blade.php`, `partials/header`, `partials/sidebar`, `partials/menu`, `partials/breadcrumb`, `grid/table`, `widgets/info-box`, `widgets/box`, `form` | `src/App.jsx`, `src/components.jsx` |

Les adaptations LyuX communes (largeur du menu, thème sombre, coque) sont regroupées dans
`src/styles.css`, chargé **après** la feuille d'origine afin de ne pas altérer le code copié.
Les styles propres à chaque domaine vivent dans le dossier de la page concernée. Les icônes
utilisent les classes `icon-*` de Font Awesome fournies par Open Admin (`src/icons.jsx`),
sans emoji.

## Démarrage

```bash
cd apps/admin-ui
npm install
npm run dev
```

Le serveur de développement écoute sur `http://localhost:5173`.

## Construction

```bash
npm run build
npm run preview
```

Les fichiers de production sont générés dans `dist/`. Comme chaque domaine a sa propre URL,
un serveur statique doit réécrire les chemins inconnus vers `index.html` (le serveur de
développement Vite le fait déjà).

## Navigation

| Domaine | Section | Contenu |
| --- | --- | --- |
| Vue d'ensemble | Tableau de bord | Indicateurs, activité, état du système, actions rapides |
| Infrastructure | Parc & salles | Bâtiments, salles, grille de postes, réveil WOL simulé |
| Infrastructure | Pilotage & mises à jour | Versions serveur/client, diffusion simulée, état du parc, lien vers Paquets & versions |
| Infrastructure | Paquets & versions | Registre des versions, manifeste signé, artefacts et politique de mise à jour |
| Pédagogie | Utilisateurs | Comptes élèves/personnels, classes et groupes de TP |
| Pédagogie | Logiciels | Liste compacte de noms, fiche détaillée à droite, arguments de lancement, catégories Proton et Wine |
| Sécurité | Identité & accès | Utilisateurs, rôles, matrice de permissions |
| Système | Intégrations | Services connectés, extensions, principes d'architecture |
| Système | Réglages | Paramètres généraux, mises à jour, sécurité |

## Structure

```
apps/admin-ui/
├── index.html
├── vite.config.js
├── package.json
└── src/
    ├── main.jsx          # Point d'entrée React + import des styles Open Admin
    ├── App.jsx           # Coque Open Admin, routage, notifications, thème
    ├── components.jsx    # Composants partagés portés depuis les vues Blade
    ├── icons.jsx         # Traduction des noms LyuX vers les classes icon-* Font Awesome
    ├── styles.css        # Ajustements communs et coque (chargés après le thème d'origine)
    ├── data/mock.js      # Jeu de données simulé
    ├── vendor/open-admin/# Code frontend Open Admin récupéré tel quel (MIT)
    ├── vendor/fontawesome/# Polices et licence Font Awesome
    └── pages/
        ├── Dashboard/    # index.jsx + components/ + Dashboard.css
        ├── Parc/         # index.jsx + components/ + Parc.css
        ├── Pilotage/     # index.jsx + components/ + Pilotage.css
        ├── Paquets/      # index.jsx + components/ + Paquets.css
        ├── Utilisateurs/ # index.jsx + components/ + Utilisateurs.css
        ├── Logiciels/    # index.jsx + components/ + Logiciels.css
        ├── Identite/     # index.jsx + components/ + Identite.css
        ├── Integrations/ # index.jsx + components/ + Integrations.css
        └── Reglages/     # index.jsx + components/ + Reglages.css
```

Chaque dossier de page est autonome : `index.jsx` assemble la page, `components/`
contient ses composants locaux et `*.css` ses seuls styles spécifiques. Les composants
communs et la coque restent dans `src/components.jsx` et `src/styles.css`.

## Page Logiciels

La page `/logiciels/` remplace l'ancien tableau du catalogue par une liste de **noms
d'applications uniquement**, alignée sur le comportement des postes dans une salle :

- la liste occupe une colonne étroite et la fiche prend le reste de la largeur ;
- la première application est sélectionnée par défaut (`LibreOffice` dans le jeu de données simulé) ;
- cliquer sur un nom sélectionne l'application et met à jour le panneau de droite ;
- la recherche et le filtre par catégorie portent uniquement sur cette liste ; si l'application
  sélectionnée est masquée par un filtre, la première application visible devient la sélection ;
- la fiche de droite affiche la description, la catégorie, la version, la taille, le format,
  la source, la licence, les **arguments de lancement**, le public cible, le nombre de postes
  équipés, les dates de déploiement et de mise à jour, la note d'administration, ainsi que
  les actions `Déployer` et `Modifier` (simulées) ;
- l'ancien bloc « Politique d'installation / Installation autonome » a été retiré de la page.

La modale « Ajouter un logiciel » demande désormais le **lien du logiciel**, la **source à
consulter**, la **dernière version connue**, la catégorie et les **arguments de lancement**.
Les catégories sont celles du catalogue, y compris **Proton** et **Wine**. Le bouton
« Vérifier » renvoie une version simulée : aucun site n'est interrogé. La fiche ajoutée
apparaît immédiatement dans la liste et devient la sélection courante, mais reste en mémoire
jusqu'au rechargement.

Le jeu de données reprend les logiciels prévus dans
[`../../../lyux-desktop/docs/logiciels-compatibilite.md`](../../../lyux-desktop/docs/logiciels-compatibilite.md) :
bureautique, Internet, NSI/SNT, sciences, création, impression 3D, ainsi que les entrées
`Proton (Steam Play)` et `Régressi` classées respectivement dans Proton et Wine. Les champs
complémentaires sont définis dans `apps` (`src/data/mock.js`). Aucune action n'est envoyée
à l'API. La piste technique pour une vraie détection de versions côté serveur est décrite
dans [`../../docs/catalogue-logiciels-detection.md`](../../docs/catalogue-logiciels-detection.md).

## Page Paquets & versions

Cette page est la traduction visuelle de l'ADR-019. Elle reste entièrement simulée : aucune
requête vers `lyux-api`, aucun dépôt de fichiers, aucune signature calculée. Les données
viennent de `releases`, `releasePolicy` et `registryStatus` dans `src/data/mock.js`.

- **Registre des versions** : recherche et filtre par famille, tableau des versions
  (`client`, `os`, `logiciel`) avec canal, état (`Publiée`, `Brouillon`, `Retirée`) et date.
  La sélection d'une ligne met à jour le panneau de droite : empreinte du manifeste,
  artefacts, taille, SHA-256 et action adaptée à l'état (`Publier`, `Planifier`, `Restaurer`).
- **Manifeste signé** : récapitulatif de l'algorithme d'empreinte (SHA-256), de la signature
  détachée (Ed25519), du stockage et du chemin d'accès API. Le client refuse un artefact
  dont l'empreinte ou la signature ne correspond pas.
- **Politique de mise à jour** : application automatique, canal suivi, fenêtre de
  maintenance, validation administrative, retour arrière, artefacts signés uniquement
  (non négociable) et périmètre par salle. La route future est
  `PUT /api/v1/updates/policy`.

Les quatre points encore à trancher dans l'ADR-019 (format de Fastpack, périmètre de la mise
à jour OS, accès Internet ou LAN, automatique ou validé) ne sont pas préjugés : les artefacts
simulés couvrent plusieurs formats et la politique par défaut reste sur une application
manuelle par salle.

## Conventions

- Interface en français.
- Aucun emoji : les icônes proviennent de la police Font Awesome d'Open Admin.
- Aucun appel réseau : le prototype reste détaché de l'API FastAPI et de Docker.
- Toute modification des fichiers sous `src/vendor/` doit conserver les avis de licence.
