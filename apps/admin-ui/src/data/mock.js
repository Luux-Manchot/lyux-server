// Données simulées — prototype visuel uniquement, aucune connexion à l'API LyuX.

export const buildings = [
  { id: 'BAT-A', name: 'Bâtiment A', description: 'Administration et accueil' },
  { id: 'BAT-B', name: 'Bâtiment B', description: 'Enseignement général et NSI' },
  { id: 'BAT-C', name: 'Bâtiment C', description: 'Pôle Sciences et Informatique' },
  { id: 'BAT-D', name: 'Bâtiment D', description: 'Ateliers technologiques' },
  { id: 'BAT-E', name: 'Bâtiment E', description: 'Arts et langues vivantes' },
  { id: 'BAT-F', name: 'Bâtiment F', description: 'CDI et espace multimédia' },
  { id: 'BAT-G', name: 'Bâtiment G', description: 'Gymnase et vie associative' },
]

export const rooms = [
  { id: 'C14', buildingId: 'BAT-C', profile: 'nsi', capacity: 24, teacher: '' },
  { id: 'C12', buildingId: 'BAT-C', profile: 'standard', capacity: 24, teacher: '' },
  { id: 'B204', buildingId: 'BAT-B', profile: 'standard', capacity: 24, teacher: 'thomas.durand' },
  { id: 'S102', buildingId: 'BAT-B', profile: 'sciences', capacity: 24, teacher: 'sophie.leroy' },
  { id: 'A101', buildingId: 'BAT-A', profile: 'standard', capacity: 16, teacher: '' },
  { id: 'F205', buildingId: 'BAT-F', profile: 'multimedia', capacity: 20, teacher: '' },
  { id: 'D110', buildingId: 'BAT-D', profile: 'atelier', capacity: 18, teacher: '' },
]

// `lastSeen` et `uptime` alimentent le panneau de détail des postes dans une salle.
export const machines = [
  { id: 'pc-01', hostname: 'LyuX-C14-PC01', room: 'C14', ip: '192.168.10.13', mac: '08:00:27:f0:45:15', status: 'online', session: 'Session libre', version: '1.4.2', build: '20261120', updates: 0, lastSeen: 'Aujourd’hui, 09:41', uptime: '4 j 12 h' },
  { id: 'pc-02', hostname: 'LyuX-C14-PC02', room: 'C14', ip: '192.168.10.14', mac: '08:00:27:f0:45:16', status: 'online', session: 'lucas.martin', version: '1.4.2', build: '20261120', updates: 0, lastSeen: 'Aujourd’hui, 09:38', uptime: '6 j 03 h' },
  { id: 'pc-03', hostname: 'C14-PC03', room: 'C14', ip: '192.168.10.15', mac: 'f8:09:d2:06:5e:06', status: 'offline', session: 'Aucune', version: '1.3.8', build: '20261002', updates: 12, lastSeen: 'Hier, 17:05', uptime: '—' },
  { id: 'pc-04', hostname: 'LyuX-C14-PC04', room: 'C14', ip: '192.168.10.16', mac: '08:00:27:a1:b2:c4', status: 'online', session: 'emma.bernard', version: '1.4.2', build: '20261120', updates: 0, lastSeen: 'Aujourd’hui, 09:40', uptime: '2 j 08 h' },
  { id: 'pc-05', hostname: 'LyuX-C12-PC01', room: 'C12', ip: '192.168.10.20', mac: '08:00:27:a1:b2:c3', status: 'offline', session: 'Aucune', version: '1.3.8', build: '20261002', updates: 9, lastSeen: '12 nov. 2026, 16:12', uptime: '—' },
  { id: 'pc-06', hostname: 'b204-prof', room: 'B204', ip: '192.168.10.21', mac: '08:00:27:c4:d5:e6', status: 'online', session: 'thomas.durand', version: '1.4.2', build: '20261120', updates: 0, lastSeen: 'Aujourd’hui, 09:15', uptime: '9 j 01 h' },
  { id: 'pc-07', hostname: 'b204-pc01', room: 'B204', ip: '192.168.10.50', mac: '08:00:27:c4:d5:e7', status: 'online', session: 'lucas.martin', version: '1.4.2', build: '20261120', updates: 0, lastSeen: 'Aujourd’hui, 09:44', uptime: '18 j 06 h' },
  { id: 'pc-08', hostname: 'b204-pc02', room: 'B204', ip: '192.168.10.51', mac: '08:00:27:c4:d5:e8', status: 'online', session: 'emma.bernard', version: '1.3.8', build: '20261002', updates: 12, lastSeen: 'Aujourd’hui, 09:33', uptime: '1 j 19 h' },
  { id: 'pc-09', hostname: 's102-prof', room: 'S102', ip: '192.168.10.30', mac: '08:00:27:f7:e8:d9', status: 'online', session: 'sophie.leroy', version: '1.4.2', build: '20261120', updates: 0, lastSeen: 'Aujourd’hui, 09:20', uptime: '7 j 11 h' },
  { id: 'pc-10', hostname: 's102-pc01', room: 'S102', ip: '192.168.10.52', mac: '08:00:27:f7:e8:da', status: 'online', session: 'hugo.dubois', version: '1.4.2', build: '20261120', updates: 0, lastSeen: 'Aujourd’hui, 09:42', uptime: '3 j 05 h' },
  { id: 'pc-11', hostname: 's102-pc02', room: 'S102', ip: '192.168.10.53', mac: '08:00:27:f7:e8:db', status: 'offline', session: 'Aucune', version: '1.3.8', build: '20261002', updates: 8, lastSeen: 'Hier, 16:48', uptime: '—' },
  { id: 'pc-12', hostname: 'a101-pc01', room: 'A101', ip: '192.168.10.60', mac: '08:00:27:11:22:33', status: 'online', session: 'Session libre', version: '1.4.2', build: '20261120', updates: 0, lastSeen: 'Aujourd’hui, 08:57', uptime: '5 j 22 h' },
]

export const classes = [
  { id: '1G1', name: 'Première Générale 1', level: 'Première', room: 'B204', students: 24, subgroups: ['Groupe A (TP)', 'Groupe B (TP)', 'Spécialité NSI'], teachers: ['thomas.durand'] },
  { id: '1G2', name: 'Première Générale 2', level: 'Première', room: 'S102', students: 22, subgroups: ['Groupe Physique', 'Groupe SVT'], teachers: ['sophie.leroy'] },
  { id: 'TG1', name: 'Terminale Générale 1', level: 'Terminale', room: 'B204', students: 28, subgroups: ['Spécialité NSI', 'Spécialité Maths'], teachers: ['thomas.durand'] },
  { id: '2NDE3', name: 'Seconde 3', level: 'Seconde', room: 'B204', students: 32, subgroups: ['Groupe 1 (SNT)', 'Groupe 2 (SNT)'], teachers: ['thomas.durand', 'sophie.leroy'] },
]

export const users = [
  { id: 'u-01', username: 'thomas.durand', displayName: 'Thomas Durand', role: 'enseignant', group: 'Maths / NSI', classe: 'TG1', status: 'active', lastLogin: 'Aujourd’hui, 08:42' },
  { id: 'u-02', username: 'sophie.leroy', displayName: 'Sophie Leroy', role: 'enseignant', group: 'Physique / SVT', classe: '1G2', status: 'active', lastLogin: 'Aujourd’hui, 09:15' },
  { id: 'u-03', username: 'lucas.martin', displayName: 'Lucas Martin', role: 'eleve', group: 'Groupe A (TP)', classe: '1G1', status: 'active', lastLogin: 'Aujourd’hui, 08:51' },
  { id: 'u-04', username: 'emma.bernard', displayName: 'Emma Bernard', role: 'eleve', group: 'Groupe B (TP)', classe: '1G1', status: 'active', lastLogin: 'Aujourd’hui, 08:53' },
  { id: 'u-05', username: 'hugo.dubois', displayName: 'Hugo Dubois', role: 'eleve', group: 'Groupe Physique', classe: '1G2', status: 'active', lastLogin: 'Hier, 16:20' },
  { id: 'u-06', username: 'lea.thomas', displayName: 'Léa Thomas', role: 'eleve', group: 'Groupe SVT', classe: '1G2', status: 'disabled', lastLogin: '12 nov. 2026' },
  { id: 'u-07', username: 'camille.rousseau', displayName: 'Camille Rousseau', role: 'viesco', group: 'Vie scolaire', classe: '—', status: 'active', lastLogin: 'Aujourd’hui, 07:58' },
  { id: 'u-08', username: 'alex.direction', displayName: 'Alexandre Moreau', role: 'administration', group: 'Direction', classe: '—', status: 'active', lastLogin: 'Aujourd’hui, 08:05' },
]

export const roles = [
  { id: 'admin', name: 'Administrateur', description: 'Accès complet au serveur et aux outils système', members: 2 },
  { id: 'direction', name: 'Direction', description: 'Pilotage pédagogique et rapports consolidés', members: 1 },
  { id: 'enseignant', name: 'Enseignant', description: 'Classes, partages pédagogiques et logiciels', members: 2 },
  { id: 'viesco', name: 'Vie scolaire', description: 'Suivi des élèves et des inscriptions', members: 1 },
  { id: 'eleve', name: 'Élève', description: 'Poste personnel et ressources de sa classe', members: 4 },
]

export const permissionMatrix = [
  { feature: 'Tableau de bord', admin: true, direction: true, enseignant: true, viesco: true, eleve: false },
  { feature: 'Parc & salles', admin: true, direction: false, enseignant: false, viesco: false, eleve: false },
  { feature: 'Pilotage des mises à jour', admin: true, direction: false, enseignant: false, viesco: false, eleve: false },
  { feature: 'Utilisateurs & classes', admin: true, direction: true, enseignant: true, viesco: true, eleve: false },
  { feature: 'Logiciels', admin: true, direction: true, enseignant: true, viesco: false, eleve: false },
  { feature: 'Comptes utilisateurs', admin: true, direction: true, enseignant: false, viesco: true, eleve: false },
  { feature: 'Rôles & permissions', admin: true, direction: false, enseignant: false, viesco: false, eleve: false },
  { feature: 'Intégrations', admin: true, direction: false, enseignant: false, viesco: false, eleve: false },
  { feature: 'Réglages système', admin: true, direction: false, enseignant: false, viesco: false, eleve: false },
]

// Catalogue prévisionnel : les logiciels sont repris de la matrice de
// compatibilité `lyux-desktop/docs/logiciels-compatibilite.md`. Les champs
// complémentaires (dont `launchArgs`) alimentent la fiche de droite.
// Toutes ces valeurs sont simulées.
const defaultApp = {
  source: 'Dépôt Debian Trixie',
  format: 'Paquet .deb',
  license: 'À vérifier',
  updatedAt: '—',
  deployedAt: 'Non déployé',
  installed: '0 / 0 postes',
  notes: 'Fiche issue du catalogue prévisionnel.',
  launchArgs: '',
}

const app = (data) => ({ ...defaultApp, ...data })

export const apps = [
  app({ id: 'libreoffice', name: 'LibreOffice', category: 'Bureautique', version: '24.8.3', target: 'Tous les postes', status: 'deployed', size: '312 Mo', description: 'Suite bureautique : traitement de texte, tableur, présentation et dessin.', license: 'MPL 2.0', updatedAt: '18 nov. 2026', deployedAt: '12 nov. 2026', installed: '112 / 118 postes', notes: 'Modèles de l’établissement inclus dans l’image LyuX.', launchArgs: '--norestore' }),
  app({ id: 'onlyoffice', name: 'OnlyOffice', category: 'Bureautique', version: '8.1.0', target: 'Tous les postes', status: 'pending', size: '286 Mo', description: 'Alternative à Microsoft Office, proposée en complément de LibreOffice.', source: 'Site officiel', license: 'AGPL-3.0', notes: 'En attente de validation pédagogique.' }),
  app({ id: 'okular', name: 'Okular', category: 'Bureautique', version: '1.11.2', target: 'Tous les postes', status: 'draft', size: '26 Mo', description: 'Lecture et annotation des documents PDF.', license: 'GPL-2.0', notes: 'Remplacement d’Adobe Acrobat Reader.' }),
  app({ id: 'firefox', name: 'Firefox ESR', category: 'Internet', version: '128.4.0', target: 'Tous les postes', status: 'deployed', size: '92 Mo', description: 'Navigateur web en version ESR, avec extensions pédagogiques filtrées.', license: 'MPL 2.0', updatedAt: '05 nov. 2026', deployedAt: '09 nov. 2026', installed: '118 / 118 postes', notes: 'Version figée pour éviter les changements d’interface en cours d’année.', launchArgs: '--new-window https://lyux.lan' }),
  app({ id: 'chromium', name: 'Chromium', category: 'Internet', version: '130.0.0', target: 'Tous les postes', status: 'pending', size: '118 Mo', description: 'Navigateur de secours pour les sites qui demandent Chromium.', license: 'BSD-3-Clause', notes: 'Profils à cadrer avant déploiement.' }),
  app({ id: 'capytale', name: 'Capytale / Basthon', category: 'Internet', version: '2026.11', target: 'Bâtiment C', status: 'pending', size: 'Service web', description: 'Environnements de programmation en ligne utilisés en NSI.', source: 'Service web', format: 'Navigateur', notes: 'Aucun artefact local : accès via Firefox ESR.' }),
  app({ id: 'vscode', name: 'Visual Studio Code', category: 'Développement', version: '1.94.2', target: 'Bâtiment C', status: 'deployed', size: '148 Mo', description: 'Éditeur de code utilisé en NSI et pour les projets de développement.', source: 'Paquet maison LyuX', license: 'MIT', updatedAt: '02 oct. 2026', deployedAt: '06 oct. 2026', installed: '24 / 118 postes', notes: 'Extensions Python et Git préconfigurées par la direction.', launchArgs: '--new-window' }),
  app({ id: 'python', name: 'Python 3.13', category: 'Développement', version: '3.13.0', target: 'Spé NSI', status: 'deployed', size: '64 Mo', description: 'Interpréteur Python et bibliothèques scientifiques pour la NSI.', license: 'PSF', updatedAt: '10 nov. 2026', deployedAt: '13 nov. 2026', installed: '24 / 118 postes', notes: 'Modules numpy, matplotlib et pygame disponibles par défaut.', launchArgs: '-u' }),
  app({ id: 'sqlite', name: 'SQLite', category: 'Développement', version: '3.47.0', target: 'Spé NSI', status: 'pending', size: '8 Mo', description: 'Base de données légère pour les cours de NSI et SNT.', license: 'Domaine public', notes: 'Remplace Microsoft Access pour l’initiation.' }),
  app({ id: 'thonny', name: 'Thonny', category: 'Éducation', version: '4.1.4', target: 'Seconde / Première', status: 'deployed', size: '31 Mo', description: 'Environnement de programmation simplifié pour les élèves débutants.', license: 'MIT', updatedAt: '21 oct. 2026', deployedAt: '24 oct. 2026', installed: '46 / 118 postes', notes: 'Réglé sur l’interpréteur Python 3.13 du parc.' }),
  app({ id: 'scratch', name: 'Scratch 3', category: 'Éducation', version: '3.29.0', target: 'Bâtiment F', status: 'pending', size: '78 Mo', description: 'Programmation visuelle par blocs pour l’initiation à l’algorithmique.', source: 'Flatpak (Flathub)', format: 'Flatpak', license: 'GPL-2.0', updatedAt: '12 nov. 2026', notes: 'En attente de validation pour le bâtiment F.' }),
  app({ id: 'geogebra', name: 'GeoGebra', category: 'Éducation', version: '6.0.80', target: 'Toutes les salles', status: 'pending', size: '94 Mo', description: 'Géométrie dynamique et algèbre, en application ou dans le navigateur.', source: 'Site officiel', format: 'Paquet .deb', license: 'Licence éducation', notes: 'Fonctionnement confirmé sur la salle pilote.' }),
  app({ id: 'xcas', name: 'Xcas', category: 'Éducation', version: '1.9.0', target: 'Mathématiques', status: 'pending', size: '42 Mo', description: 'Calcul formel et algèbre symbolique pour le lycée.', license: 'GPL-2.0' }),
  app({ id: 'scilab', name: 'Scilab', category: 'Éducation', version: '2024.1.0', target: 'Mathématiques', status: 'pending', size: '210 Mo', description: 'Environnement de calcul numérique pour les mathématiques et la physique.', source: 'Site officiel', format: 'Binaire officiel', license: 'CeCILL' }),
  app({ id: 'octave', name: 'Octave', category: 'Éducation', version: '9.2.0', target: 'Mathématiques', status: 'pending', size: '96 Mo', description: 'Alternative libre à MATLAB pour le calcul numérique.', license: 'GPL-3.0' }),
  app({ id: 'packettracer', name: 'Cisco Packet Tracer', category: 'Éducation', version: '8.2.2', target: 'Bâtiment C', status: 'draft', size: '184 Mo', description: 'Simulateur de réseaux pour les cours de SNT et de NSI.', source: 'Cisco NetAcad', format: 'Binaire officiel', license: 'Compte NetAcad requis', notes: 'Nécessite un compte Cisco NetAcad.' }),
  app({ id: 'filius', name: 'Filius', category: 'Éducation', version: '1.6.1', target: 'Bâtiment C', status: 'pending', size: '18 Mo', description: 'Simulateur de réseaux léger en Java.', format: 'Application Java', license: 'GPL-2.0' }),
  app({ id: 'mathgraph32', name: 'MathGraph32', category: 'Éducation', version: '8.5.0', target: 'Mathématiques', status: 'draft', size: '22 Mo', description: 'Construction géométrique dynamique en Java.', source: 'Site officiel', format: 'Application Java', license: 'Licence éducation' }),
  app({ id: 'tracker', name: 'Tracker', category: 'Éducation', version: '5.2.0', target: 'Sciences', status: 'pending', size: '64 Mo', description: 'Analyse vidéo et modélisation des mouvements en physique.', format: 'Application Java', license: 'GPL-2.0' }),
  app({ id: 'avogadro', name: 'Avogadro', category: 'Éducation', version: '1.5.0', target: 'Sciences', status: 'pending', size: '88 Mo', description: 'Visualisation et modélisation moléculaire en chimie.', license: 'GPL-2.0' }),
  app({ id: 'stellarium', name: 'Stellarium', category: 'Éducation', version: '24.2.0', target: 'Sciences', status: 'pending', size: '112 Mo', description: 'Planétarium virtuel pour les cours de sciences.', license: 'GPL-2.0' }),
  app({ id: 'jmol', name: 'Jmol', category: 'Éducation', version: '16.3.0', target: 'Sciences', status: 'pending', size: '14 Mo', description: 'Visualisation 3D des molécules en chimie.', format: 'Application Java', license: 'LGPL-2.1' }),
  app({ id: 'qgis', name: 'QGIS', category: 'Éducation', version: '3.40.0', target: 'Sciences', status: 'pending', size: '242 Mo', description: 'Système d’information géographique pour la géographie et les sciences.', license: 'GPL-2.0' }),
  app({ id: 'kicad', name: 'KiCad', category: 'Éducation', version: '9.0.0', target: 'Bâtiment D', status: 'pending', size: '196 Mo', description: 'Conception de circuits imprimés pour l’électronique.', license: 'GPL-3.0', notes: 'Remplace Proteus et Multisim pour l’initiation.' }),
  app({ id: 'blender', name: 'Blender', category: 'Création', version: '4.3.2', target: 'Bâtiment D', status: 'pending', size: '412 Mo', description: 'Suite de modélisation 3D pour les ateliers technologiques.', source: 'Flatpak (Flathub)', format: 'Flatpak', license: 'GPL-3.0', updatedAt: '16 oct. 2026', notes: 'Validation en attente : artefact volumineux à distribuer par salle.', launchArgs: '--factory-startup' }),
  app({ id: 'freecad', name: 'FreeCAD', category: 'Création', version: '1.0.0', target: 'Bâtiment D', status: 'pending', size: '328 Mo', description: 'Modélisation 3D paramétrique pour l’initiation industrielle.', license: 'LGPL-2.1', notes: 'Alternatives à SolidWorks, Inventor et CATIA pour l’initiation.' }),
  app({ id: 'cura', name: 'Cura', category: 'Création', version: '5.8.0', target: 'Bâtiment D', status: 'pending', size: '144 Mo', description: 'Tranchage des modèles pour l’impression 3D.', source: 'Site officiel', format: 'AppImage', license: 'AGPL-3.0' }),
  app({ id: 'prusaslicer', name: 'PrusaSlicer', category: 'Création', version: '2.9.0', target: 'Bâtiment D', status: 'pending', size: '128 Mo', description: 'Tranchage des modèles pour l’impression 3D.', source: 'Site officiel', format: 'AppImage', license: 'AGPL-3.0' }),
  app({ id: 'gimp', name: 'GIMP', category: 'Création', version: '2.10.36', target: 'Bâtiment E', status: 'draft', size: '186 Mo', description: 'Éditeur d’images pour les ateliers créatifs et le club multimédia.', source: 'Flatpak (Flathub)', format: 'Flatpak', license: 'GPL-3.0', updatedAt: '28 sept. 2026', notes: 'Brouillon : non diffusé aux postes tant que le catalogue n’est pas validé.', launchArgs: '--no-splash' }),
  app({ id: 'audacity', name: 'Audacity', category: 'Multimédia', version: '3.7.0', target: 'Bâtiment E', status: 'pending', size: '58 Mo', description: 'Édition audio pour les ateliers créatifs et le club multimédia.', license: 'GPL-2.0' }),
  app({ id: 'vlc', name: 'VLC media player', category: 'Multimédia', version: '3.0.21', target: 'Tous les postes', status: 'deployed', size: '48 Mo', description: 'Lecteur multimédia pour les ressources pédagogiques locales et en réseau.', license: 'GPL-2.0', updatedAt: '08 nov. 2026', deployedAt: '11 nov. 2026', installed: '118 / 118 postes', notes: 'Accès au cache réseau du serveur activé.', launchArgs: '--fullscreen' }),
  app({ id: 'proton', name: 'Proton (Steam Play)', category: 'Proton', version: '9.0.4', target: 'Salle pilote', status: 'draft', size: '410 Mo', description: 'Couche de compatibilité Windows à tester sur la salle pilote.', source: 'Steam Play', format: 'Runtime', license: 'GPL-2.0', notes: 'Aucun déploiement prévu avant validation : artefacts et droits à vérifier.', launchArgs: 'STEAM_COMPAT_DATA_PATH=/srv/lyux/proton %command%' }),
  app({ id: 'regressi', name: 'Régressi', category: 'Wine', version: '5.0.0', target: 'Bâtiment B', status: 'draft', size: '72 Mo', description: 'Exploitation et modélisation de mesures en physique-chimie.', source: 'Site officiel', format: 'Exécutable Windows', license: 'Licence commerciale', notes: 'Test sous Wine : résultats variables selon les versions.', launchArgs: 'wine /opt/regressi/Regressi.exe' }),
]

export const integrations = [
  { id: 'samba', name: 'Samba 4 Active Directory', category: 'Identité', description: 'Annuaire LDAP centralisé et partages CIFS des cours, devoirs et dossiers personnels.', status: 'active', detail: 'Ports 389 / 445 · socle système' },
  { id: 'kuma', name: 'Uptime Kuma', category: 'Supervision', description: 'Surveillance temps réel de l’infrastructure, sondes ICMP et alertes de panne.', status: 'active', detail: 'Version 2.5 · port 3001' },
  { id: 'glpi', name: 'GLPI', category: 'Inventaire', description: 'Inventaire automatique du parc, tickets d’incidents matériel et suivi des pannes.', status: 'active', detail: 'Port 8085' },
  { id: 'cockpit', name: 'Cockpit natif', category: 'Système', description: 'Console système de l’appliance : services, journal, réseau et stockage.', status: 'active', detail: 'Port 9090 · conservé' },
  { id: 'hub', name: 'Hub LyuX', category: 'Interface', description: 'Point d’entrée unifié des modules d’administration de l’établissement.', status: 'active', detail: 'Port 8086 · conteneur dédié' },
  { id: 'proxy', name: 'Cache APT', category: 'Infrastructure', description: 'Mise en cache des paquets pour accélérer les mises à jour du parc client.', status: 'active', detail: 'Port 3142' },
  { id: 'sso', name: 'Authentification SSO', category: 'Identité', description: 'Connexion unique au panneau et aux services via l’annuaire de l’établissement.', status: 'planned', detail: 'Non configuré' },
]

export const activity = [
  { id: 'a-1', time: '09:42', title: 'Mise à jour diffusée', detail: '12 postes du bâtiment C', tone: 'success', icon: 'download' },
  { id: 'a-2', time: '09:18', title: 'Nouveau compte créé', detail: 'lucas.martin · Élève · 1G1', tone: 'info', icon: 'users' },
  { id: 'a-3', time: '08:56', title: 'Poste hors ligne', detail: 'C14-PC03 · absence détectée', tone: 'warning', icon: 'monitor' },
  { id: 'a-4', time: '08:30', title: 'Sauvegarde terminée', detail: 'Configuration du serveur', tone: 'success', icon: 'checkCircle' },
  { id: 'a-5', time: 'Hier, 17:12', title: 'Droits modifiés', detail: 'Rôle Enseignant · partages de classe', tone: 'info', icon: 'shield' },
]

export const settings = {
  schoolName: 'Lycée Opération Manchot',
  schoolYear: '2026 – 2027',
  contact: 'administration@lyux.lan',
  timezone: 'Europe/Paris',
  language: 'Français',
  enrollment: true,
  autoUpdate: true,
  updateWindow: '22:00 – 05:00',
  retention: 90,
  sessionTimeout: 45,
}

export const serverInfo = {
  version: '1.4.2',
  build: '20261122',
  repository: 'FlowCreativeStudio/OperationManchot',
  status: 'À jour',
  clientTarget: '1.4.2',
  uptime: '18 jours, 6 heures',
}

// Registre des versions — données simulées pour la page « Paquets & versions ».
// La structure reprend celle de l'ADR-019 : version, build, canal, famille,
// état de publication, artefacts avec empreinte et signature détachée.
export const releases = [
  {
    id: 'rel-client-142',
    version: '1.4.2',
    build: '20261122',
    channel: 'stable',
    family: 'client',
    state: 'published',
    target: 'Tous les postes',
    publishedAt: '22 nov. 2026, 08:10',
    author: 'alex.direction',
    notes: 'Correctif du verrouillage kiosk et synchronisation des profils.',
    signature: 'Vérifiée',
    manifestHash: '9f2c41d8e7a6b0351c4e8d90a2f67b135be0c984d7f2a1e6c3b8095f4a2d17e0',
    artifacts: [
      { name: 'lyux-client_1.4.2_amd64.deb', type: 'deb', size: '48,2 Mo', sha256: '9f2c41d8e7a6b0351c4e8d90a2f67b135be0c984d7f2a1e6c3b8095f4a2d17e0' },
      { name: 'lyux-kiosk-theme_1.4.2.tar.xz', type: 'configuration', size: '2,4 Mo', sha256: 'b41e7c09d3a85f62e1c9407db6a2f8e5039d71c4a6b8e2f90d5c3a17e8b46029' },
    ],
  },
  {
    id: 'rel-os-trixie-138',
    version: '13.8.0',
    build: '20261120',
    channel: 'stable',
    family: 'os',
    state: 'published',
    target: 'Bâtiments A à G',
    publishedAt: '20 nov. 2026, 14:35',
    author: 'alex.direction',
    notes: 'Image Debian Trixie netinst et profil preseed de l’établissement.',
    signature: 'Vérifiée',
    manifestHash: '3a7d90c1f6b28e5409de2a71c430b8f65e0d9c2a7b14f8063d5e9a2c71b0f486',
    artifacts: [
      { name: 'debian-13.8.0-amd64-netinst.iso', type: 'image', size: '631 Mo', sha256: '3a7d90c1f6b28e5409de2a71c430b8f65e0d9c2a7b14f8063d5e9a2c71b0f486' },
      { name: 'preseed-lyux-trixie.cfg', type: 'configuration', size: '14 Ko', sha256: 'c08f2a6d91b4e7350a2d8f6c34e19b05a7d2e8c9403fb615e2c7a90d84b13f6e' },
    ],
  },
  {
    id: 'rel-apps-flatpak',
    version: '2026.11',
    build: '20261118',
    channel: 'stable',
    family: 'logiciel',
    state: 'published',
    target: 'Catalogue contrôlé',
    publishedAt: '18 nov. 2026, 11:02',
    author: 'alex.direction',
    notes: 'Lot Flatpak validé : Blender, Audacity, GIMP et Krita.',
    signature: 'Vérifiée',
    manifestHash: 'e12b7a409d6c83f51e0b2a94c7d68f350a1e9c4b27d605f83a9c1e4b70d25f86',
    artifacts: [
      { name: 'flatpak-bundle-2026.11.json', type: 'flatpak', size: '1,1 Go', sha256: 'e12b7a409d6c83f51e0b2a94c7d68f350a1e9c4b27d605f83a9c1e4b70d25f86' },
    ],
  },
  {
    id: 'rel-client-150',
    version: '1.5.0',
    build: '20261128',
    channel: 'test',
    family: 'client',
    state: 'draft',
    target: 'Bâtiment C',
    publishedAt: 'Non publié',
    author: 'alex.direction',
    notes: 'Nouveau module de rapport de version. En attente de validation.',
    signature: 'En attente',
    manifestHash: 'a05e3c92b71d486f013a9e6c2b8f5071d4e9c3a06b12f85e7c9d2a40b6f31875',
    artifacts: [
      { name: 'lyux-client_1.5.0_amd64.deb', type: 'deb', size: '51,7 Mo', sha256: 'a05e3c92b71d486f013a9e6c2b8f5071d4e9c3a06b12f85e7c9d2a40b6f31875' },
    ],
  },
  {
    id: 'rel-fastpack-21',
    version: '2.1.0',
    build: '20261126',
    channel: 'test',
    family: 'logiciel',
    state: 'draft',
    target: 'Bâtiment D',
    publishedAt: 'Non publié',
    author: 'alex.direction',
    notes: 'Lot Fastpack en attente de précision sur le format d’artefact.',
    signature: 'En attente',
    manifestHash: '7d1b6e50a2c94f83e0b7a15d2c68f4903a1e5b7d09c24f86e5a3b1c70d92f468',
    artifacts: [
      { name: 'fastpack-2.1.0.amd64.fpk', type: 'fastpack', size: '76,3 Mo', sha256: '7d1b6e50a2c94f83e0b7a15d2c68f4903a1e5b7d09c24f86e5a3b1c70d92f468' },
    ],
  },
  {
    id: 'rel-client-138',
    version: '1.3.8',
    build: '20261002',
    channel: 'stable',
    family: 'client',
    state: 'retired',
    target: 'Aucune (historique)',
    publishedAt: '2 oct. 2026, 09:20',
    author: 'alex.direction',
    notes: 'Version conservée pour retour arrière.',
    signature: 'Vérifiée',
    manifestHash: '4c9e2b706f1a8d35e0c4a97b26d51f830e7c1b4a95d206f38c7e0a1b4d95f623',
    artifacts: [
      { name: 'lyux-client_1.3.8_amd64.deb', type: 'deb', size: '45,9 Mo', sha256: '4c9e2b706f1a8d35e0c4a97b26d51f830e7c0a1b4a95d206f38c7e0a1b4d95f623' },
    ],
  },
]

export const releasePolicy = {
  autoApply: false,
  channel: 'stable',
  window: '22:00 – 05:00',
  requireApproval: true,
  rollback: true,
  signedOnly: true,
  scope: 'room',
}

export const registryStatus = {
  lastCheck: 'Aujourd’hui, 09:42',
  storage: '/srv/lyux/releases',
  signature: 'Ed25519 · clé lyux-release-2026',
  hashing: 'SHA-256',
  auth: 'Requise pour toute écriture',
  api: 'lyux-api via lyux-hub (/api)',
}
