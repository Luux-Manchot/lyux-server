# Couleurs et indicateurs d'état — panneau LyuX

Document de référence du prototype `apps/admin-ui`. Il fixe le sens de chaque couleur
et de chaque pastille affichée dans l'interface, afin que la même information ait
toujours la même apparence d'une page à l'autre.

Les couleurs sont définies une seule fois dans `apps/admin-ui/src/styles.css` :
`:root` pour le thème clair, `[data-theme='dark']` pour le thème sombre. Les composants
utilisent les variables (`--success`, `--warning`, `--success-soft`, …) et jamais de
valeur codée en dur, sauf exception de contraste documentée plus bas.

> Rappel : il s'agit d'un prototype visuel. Les états proviennent de `src/data/mock.js`
> et ne reflètent aucune mesure réelle de l'infrastructure.

## Palette

| Couleur | Thème clair | Thème sombre | Signification | Où on la voit |
| --- | --- | --- | --- | --- |
| Vert | `#00a65a` | `#4ade9a` | Nominal : en ligne, actif, à jour, terminé | Pastille « En ligne », badge « À jour », part verte de la répartition du parc |
| Gris | `#6c757d` / `#98a2b3` | `#9aa8bd` / `#71809a` | État neutre : éteint, hors ligne, désactivé, brouillon | Badge « Hors ligne », comptes désactivés, part grise de la répartition du parc |
| Jaune / ambre | `#ffc107` | `#fbbf24` | Attention : mise à jour disponible, en attente, à surveiller | Badge « 12 paquets », compteur « Mises à jour en attente », pastille ambre de la répartition |
| Rouge | `#dc3545` | `#f87171` | Erreur : incident confirmé, échec, action sensible | Toasts d'erreur, zone sensible des réglages, pastille de la cloche |
| Bleu | `#3a96ff` | `#60a5fa` | Information, sélection, opération en cours | Liens, tuile sélectionnée, boutons primaires, notification d'information |
| Violet | `#6941c6` | `#b79cff` | Identité et droits | Rôles, matrice de permissions |

Chaque couleur possède aussi un fond pâle (`--success-soft`, `--warning-soft`, …)
utilisé par les badges et les fonds de pastilles. Le vert et le jaune sont les deux
couleurs les plus importantes à lire d'un coup d'œil : elles répondent respectivement
à « ça tourne » et « ça attend une action ».

## Règles d'usage

1. **Éteint n'est pas une panne.** Un poste hors ligne est gris. Le rouge est réservé
   à un incident confirmé ou à une action irréversible. Un poste éteint la nuit ne doit
   pas déclencher d'alerte rouge.
2. **Jamais la couleur seule.** Une pastille est toujours accompagnée d'un libellé ou
   d'un nombre (« En ligne », « Hors ligne », « 2 màj ») pour rester lisible en cas de
   daltonisme ou d'impression.
3. **Pastille pleine = état courant ; barre segmentée = répartition.** On ne mélange
   pas les deux codes dans le même élément.
4. **Une seule source de vérité.** Pour ajouter un état, on ajoute une variable dans
   `styles.css`, puis on l'emploie dans les composants ; on ne duplique pas un hex.
5. **Contraste du jaune.** En thème clair, le jaune `#ffc107` est trop pâle comme texte :
   le texte des compteurs « MAJ » utilise l'ambre soutenu `#b45309` sur fond
   `--warning-soft`. En thème sombre, on reprend directement `--warning`.

## Lecture de la répartition du parc (tableau de bord)

La carte « Répartition du parc » respecte la légende affichée en haut de la carte :

- **Vert** : postes en ligne du bâtiment.
- **Gris** : postes hors ligne du bâtiment.
- **Ambre** : postes ayant au moins une mise à jour en attente (ce compte peut
  recouper les deux autres, il est donc affiché séparément).

La barre de chaque bâtiment est segmentée : la partie verte représente les postes
en ligne, la partie grise les postes hors ligne. Les trois nombres à droite donnent
le détail. Un bâtiment sans poste inventorié affiche `0` sans barre colorée.

Avec les données simulées actuelles, le bâtiment C se lit par exemple :
**3 en ligne, 2 hors ligne, 2 postes avec des mises à jour en attente**. Le bâtiment B
affiche **5 en ligne, 1 hors ligne, 2 avec mises à jour**. Les autres bâtiments n'ont
pas encore de poste dans le jeu de données.

Cette lecture se retrouve ensuite dans les autres vues :

- **Parc & salles** : l'icône et le badge de chaque tuile reprennent vert/gris ;
  l'encadré « Mises à jour » indique le nombre de paquets en attente.
- **Pilotage & mises à jour** : le badge « À jour » est vert, « N paquets » est ambre,
  le taux de synchronisation global est vert.
- **Identité & accès** : vert pour un compte actif, gris pour un compte désactivé,
  violet pour les rôles.
- **Notifications** : la pastille de la cloche est rouge tant qu'il reste des
  événements ; chaque ligne utilise l'icône vert/ambre/rouge selon sa gravité.
- **Toasts** : la bordure gauche prend la couleur du message (vert succès, bleu
  information, ambre avertissement, rouge erreur).

## Où modifier

| Besoin | Fichier |
| --- | --- |
| Changer une couleur ou ajouter un état | `apps/admin-ui/src/styles.css` (`:root` et `[data-theme='dark']`) |
| Changer la légende ou le détail par bâtiment | `apps/admin-ui/src/pages/Dashboard/components/BuildingDistribution.jsx` |
| Ajuster les styles de la répartition | `apps/admin-ui/src/pages/Dashboard/Dashboard.css` |
| Changer les états simulés | `apps/admin-ui/src/data/mock.js` |
