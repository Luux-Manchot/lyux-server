import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Avatar } from './components.jsx'
import { Icon } from './icons.jsx'
import { buildingSlug, nextBuildingId } from './data/buildings.js'
import { buildingPath, pushRoute, readRoute, roomPath, roomSlug, routePath } from './routes.js'
import BuildingModal from './pages/Parc/components/BuildingModal.jsx'
import Dashboard from './pages/Dashboard/index.jsx'
import Parc from './pages/Parc/index.jsx'
import ParcBatiment from './pages/ParcBatiment/index.jsx'
import ParcSalle from './pages/ParcSalle/index.jsx'
import Pilotage from './pages/Pilotage/index.jsx'
import Paquets from './pages/Paquets/index.jsx'
import Utilisateurs from './pages/Utilisateurs/index.jsx'
import Logiciels from './pages/Logiciels/index.jsx'
import Profils from './pages/Profils/index.jsx'
import Identite from './pages/Identite/index.jsx'
import Integrations from './pages/Integrations/index.jsx'
import Reglages from './pages/Reglages/index.jsx'
import Setup from './pages/Setup/index.jsx'
import Login from './pages/Login/index.jsx'
import { api, getToken, setToken } from './api/client.js'

// Navigation restructurée : séparation claire entre Parc, Applications/Système et Utilisateurs.
const NAV_GROUPS = [
  {
    label: "Général",
    items: [{ id: 'dashboard', label: 'Tableau de bord', icon: 'dashboard', perm: 'dashboard.view' }],
  },
  {
    label: 'Parc & Postes',
    items: [
      { id: 'parc', label: 'Bâtiments & salles', icon: 'building', perm: 'parc.view' },
      { id: 'pilotage', label: 'Postes & Mises à jour', icon: 'monitor', perm: 'parc.view' },
    ],
  },
  {
    label: 'Logiciels & Système',
    items: [
      { id: 'profils', label: 'Profils & Personnalisation', icon: 'sliders', perm: 'profiles.view' },
      { id: 'logiciels', label: 'Catalogue d’applications', icon: 'layers', perm: 'apps.view' },
      { id: 'paquets', label: 'Versions OS & Dépôt', icon: 'package', perm: 'releases.view' },
    ],
  },
  {
    label: 'Utilisateurs & Droits',
    items: [
      { id: 'utilisateurs', label: 'Utilisateurs', icon: 'users', perm: 'users.view' },
      { id: 'identite', label: 'Rôles & Permissions', icon: 'shield', perm: 'roles.view' },
    ],
  },
  {
    label: 'Administration',
    items: [
      { id: 'setup', label: 'Établissement', icon: 'graduation', perm: 'setup.manage' },
      { id: 'integrations', label: 'Services & Modules', icon: 'puzzle', perm: 'setup.manage' },
      { id: 'reglages', label: 'Paramètres serveur', icon: 'settings', perm: 'setup.manage' },
    ],
  },
]

const PAGE_PERMS = Object.fromEntries(
  NAV_GROUPS.flatMap((group) => group.items.map((item) => [item.id, item.perm])),
)

const PAGE_LABELS = Object.fromEntries(
  NAV_GROUPS.flatMap((group) => group.items.map((item) => [item.id, item.label])),
)

// Ignore les accents dans la recherche du menu (« batiment h » trouve « Bâtiment H »).
const normalize = (value) => value
  .toLowerCase()
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')

const PAGES = {
  dashboard: Dashboard,
  parc: Parc,
  pilotage: Pilotage,
  paquets: Paquets,
  utilisateurs: Utilisateurs,
  logiciels: Logiciels,
  profils: Profils,
  identite: Identite,
  setup: Setup,
  integrations: Integrations,
  reglages: Reglages,
}

export default function App() {
  const [user, setUser] = useState(null)
  const [authChecking, setAuthChecking] = useState(() => Boolean(getToken()))
  const [setupStatus, setSetupStatus] = useState(null)
  // La liste des bâtiments et salles vit ici : la sidebar, le tableau de bord,
  // la page Parc et les sous-pages lisent la même source réelle de l'API.
  const [buildings, setBuildings] = useState([])
  const [rooms, setRooms] = useState([])
  const [notifications, setNotifications] = useState([])
  const [route, setRoute] = useState(readRoute)
  const [buildingModalOpen, setBuildingModalOpen] = useState(false)
  const [newBuildingName, setNewBuildingName] = useState('')
  const [parcExpanded, setParcExpanded] = useState(() => readRoute().page === 'parc')
  const [theme, setTheme] = useState('light')
  const [sidebarOpen, setSidebarOpen] = useState(() => (
    typeof window === 'undefined' ? true : window.innerWidth >= 992
  ))
  const [toasts, setToasts] = useState([])
  const [menuQuery, setMenuQuery] = useState('')
  const [searchOpen, setSearchOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const searchInputRef = useRef(null)
  const notificationsRef = useRef(null)
  const profileRef = useRef(null)

  const activePage = PAGES[route.page] ? route.page : 'dashboard'
  const activeBuilding = route.page === 'parc' && route.child
    ? buildings.find((building) => buildingSlug(building) === route.child) || null
    : null
  const activeRoom = activeBuilding && route.room
    ? rooms.find((room) => room.buildingId === activeBuilding.id && roomSlug(room) === route.room) || null
    : null
  const pageLabel = route.page === 'parc' && route.room
    ? (activeRoom ? `Salle ${activeRoom.id}` : 'Salle introuvable')
    : (route.page === 'parc' && route.child
      ? (activeBuilding ? activeBuilding.name : 'Bâtiment introuvable')
      : PAGE_LABELS[activePage])

  const userPerms = user?.permissions && typeof user.permissions === 'object' ? user.permissions : null
  const hasPerm = useCallback((permKey) => {
    if (!permKey || !userPerms) return true
    return userPerms[permKey] !== false
  }, [userPerms])

  const normalizedQuery = normalize(menuQuery.trim())
  // Le groupe « Parc & salles » reçoit ses enfants depuis l'état partagé :
  // ajouter un bâtiment le fait apparaître immédiatement dans la sidebar.
  const visibleNav = useMemo(() => NAV_GROUPS
    .map((group) => {
      const items = group.items
        .filter((item) => hasPerm(item.perm))
        .map((item) => {
          if (item.id !== 'parc') return item
          return {
            ...item,
            children: [
              { id: 'parc', label: 'Vue d’ensemble', path: routePath('parc') },
              ...buildings.map((building) => ({
                id: buildingSlug(building),
                label: building.name,
                path: buildingPath(building),
              })),
            ],
          }
        })
      const labelMatches = (item) => normalize(item.label).includes(normalizedQuery)
        || normalize(group.label).includes(normalizedQuery)
      return {
        ...group,
        items: items
          .filter((item) => !normalizedQuery || labelMatches(item)
            || item.children?.some((child) => normalize(child.label).includes(normalizedQuery)))
          // Si seule la recherche d'un bâtiment a fait matcher le groupe,
          // on ne garde que ce bâtiment dans la liste dépliée.
          .map((item) => (!normalizedQuery || !item.children || labelMatches(item)
            ? item
            : {
              ...item,
              children: item.children.filter((child) => normalize(child.label).includes(normalizedQuery)),
            })),
      }
    })
    .filter((group) => group.items.length > 0), [buildings, normalizedQuery, hasPerm])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  // Classe de corps utilisée par la feuille de style Open Admin pour afficher
  // le menu latéral (`side-menu-open` / `aside#sidebar` / `main#main`).
  useEffect(() => {
    document.body.classList.toggle('side-menu-open', sidebarOpen)
    return () => document.body.classList.remove('side-menu-open')
  }, [sidebarOpen])

  // Synchronise l'onglet avec l'historique du navigateur (liens et boutons précédent/suivant).
  useEffect(() => {
    const onPopState = () => setRoute(readRoute())
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  // L'ancienne URL `/pedagogie/` reste valable en favori : elle ouvre désormais
  // la page Logiciels, qui a repris le catalogue de l'ancienne page.
  useEffect(() => {
    if (route.page !== 'pedagogie') return
    window.history.replaceState({ page: 'logiciels', child: null, room: null }, '', routePath('logiciels'))
    setRoute({ page: 'logiciels', child: null, room: null })
  }, [route.page])

  useEffect(() => {
    document.title = `LyuX Administration — ${pageLabel}`
  }, [pageLabel])

  // Une sous-page bâtiment ouvre toujours le groupe dans la sidebar.
  useEffect(() => {
    if (route.page === 'parc') setParcExpanded(true)
  }, [route.page])

  useEffect(() => {
    if (searchOpen) searchInputRef.current?.focus()
  }, [searchOpen])

  // Fermeture clavier et clic extérieur pour les panneaux de l'en-tête.
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        setSearchOpen(false)
        setMenuQuery('')
        setNotificationsOpen(false)
        setProfileOpen(false)
      }
    }
    const onMouseDown = (event) => {
      if (notificationsRef.current && !notificationsRef.current.contains(event.target)) {
        setNotificationsOpen(false)
      }
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false)
      }
    }
    document.addEventListener('keydown', onKeyDown)
    document.addEventListener('mousedown', onMouseDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.removeEventListener('mousedown', onMouseDown)
    }
  }, [])

  const notify = useCallback((message, tone = 'success') => {
    const id = `${Date.now()}-${Math.random()}`
    setToasts((previous) => [...previous, { id, message, tone }])
    window.setTimeout(() => {
      setToasts((previous) => previous.filter((toast) => toast.id !== id))
    }, 3800)
  }, [])

  const navigate = useCallback((page) => {
    if (!PAGES[page]) return
    pushRoute(page)
    setRoute({ page, child: null, room: null })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  const navigateBuilding = useCallback((building) => {
    if (!building) return
    const slug = buildingSlug(building)
    pushRoute('parc', slug)
    setRoute({ page: 'parc', child: slug, room: null })
    setParcExpanded(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  const navigateRoom = useCallback((building, room) => {
    if (!building || !room) return
    const child = buildingSlug(building)
    const slug = roomSlug(room)
    pushRoute('parc', child, slug)
    setRoute({ page: 'parc', child, room: slug })
    setParcExpanded(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  const openBuildingModal = useCallback(() => {
    setNewBuildingName('')
    setBuildingModalOpen(true)
  }, [])

  useEffect(() => {
    const onUnauthorized = () => {
      setToken('')
      setUser(null)
    }
    window.addEventListener('lyux:unauthorized', onUnauthorized)
    const token = getToken()
    if (!token) {
      setAuthChecking(false)
      return () => window.removeEventListener('lyux:unauthorized', onUnauthorized)
    }
    api.me()
      .then((me) => setUser(me))
      .catch(() => {
        setToken('')
        setUser(null)
      })
      .finally(() => setAuthChecking(false))
    return () => window.removeEventListener('lyux:unauthorized', onUnauthorized)
  }, [])

  const refreshServerData = useCallback(() => {
    api.getBuildings()
      .then((list) => {
        if (Array.isArray(list)) setBuildings(list)
      })
      .catch(() => {})
    api.getRooms()
      .then((list) => {
        if (Array.isArray(list)) {
          setRooms(list.map((r) => ({ ...r, buildingId: r.building_id || r.buildingId })))
        }
      })
      .catch(() => {})
    api.getSetup()
      .then((res) => setSetupStatus(res))
      .catch(() => {})
    api.dashboardSummary()
      .then((res) => {
        if (Array.isArray(res?.recent_tickets)) {
          setNotifications(res.recent_tickets.map((t) => ({
            id: t.id,
            title: t.title,
            detail: `${t.author} · ${t.status}`,
            time: t.time || '',
            tone: t.status === 'Résolu' ? 'success' : 'info',
            icon: 'info',
          })))
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (user) refreshServerData()
  }, [user, refreshServerData])

  const createBuilding = useCallback(async () => {
    const name = newBuildingName.trim()
    if (!name) {
      notify('Saisissez un nom de bâtiment.', 'warning')
      return
    }
    const id = nextBuildingId(buildings)
    const payload = {
      id,
      name,
      description: 'Ajouté depuis la console d’administration.',
    }
    try {
      const res = await api.createBuilding(payload)
      const created = res?.building || payload
      setBuildings((previous) => [...previous, created])
      setBuildingModalOpen(false)
      setNewBuildingName('')
      navigateBuilding(created)
      notify(`Bâtiment « ${name} » créé.`, 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors de la création du bâtiment.', 'danger')
    }
  }, [buildings, navigateBuilding, newBuildingName, notify])

  const ActivePage = PAGES[activePage] || Dashboard

  const handleLogout = useCallback(() => {
    api.logout().catch(() => {})
    setToken('')
    setUser(null)
    setProfileOpen(false)
  }, [])

  if (authChecking) {
    return (
      <div className="login-shell">
        <div className="card" style={{ padding: 24 }}>Vérification de la session…</div>
      </div>
    )
  }

  if (!user) {
    return <Login onSuccess={(loggedUser) => setUser(loggedUser)} />
  }

  const displayName = user.display_name || user.username || 'Administrateur'
  const roleLabel = user.effective_role_name || (user.role === 'admin' ? 'Administrateur' : user.role)
  const canAccessActivePage = hasPerm(PAGE_PERMS[activePage])

  // Titre de page / fil d'Ariane affiché dans la barre supérieure (sans « Accueil »).
  const breadcrumb = (
    <nav aria-label="breadcrumb" className="breadcrumb-nav">
      <ol className="breadcrumb">
        <li className={`breadcrumb-item ${route.page === 'parc' && route.child ? '' : 'active'}`}>
          {route.page === 'parc' && route.child ? (
            <a href={routePath('parc')} onClick={(event) => { event.preventDefault(); navigate('parc') }}>
              {PAGE_LABELS.parc}
            </a>
          ) : pageLabel}
        </li>
        {route.page === 'parc' && route.child && (
          <li className={`breadcrumb-item ${route.room ? '' : 'active'}`}>
            {route.room && activeBuilding ? (
              <a
                href={buildingPath(activeBuilding)}
                onClick={(event) => { event.preventDefault(); navigateBuilding(activeBuilding) }}
              >
                {activeBuilding.name}
              </a>
            ) : pageLabel}
          </li>
        )}
        {route.page === 'parc' && route.room && <li className="breadcrumb-item active">{pageLabel}</li>}
      </ol>
    </nav>
  )

  return (
    <div className="wrapper app-shell">
      <header className="custom-navbar navbar navbar-light bg-white p-0 align-items-stretch">
        <a
          className="navbar-brand menu-width container-md bg-semi-dark text-center"
          href={routePath('dashboard')}
          onClick={(event) => { event.preventDefault(); navigate('dashboard') }}
        >
          <span className="short">LyuX</span>
          <span className="long">LyuX Administration</span>
        </a>

        <div className="d-flex flex-fill header-items">
          <button
            type="button"
            className="menu-toggle"
            id="menu-toggle"
            aria-controls="menu"
            aria-expanded={sidebarOpen}
            aria-label={sidebarOpen ? 'Masquer la navigation' : 'Afficher la navigation'}
            onClick={() => setSidebarOpen((previous) => !previous)}
          >
            <Icon name="menu" size={19} />
          </button>

          {breadcrumb}

          <ul className="nav navbar-nav header-right">
            <li className="nav-item header-search">
              {searchOpen && (
                <input
                  ref={searchInputRef}
                  className="form-control header-search-input"
                  type="search"
                  value={menuQuery}
                  placeholder="Rechercher un menu…"
                  aria-label="Rechercher un menu"
                  onChange={(event) => setMenuQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && visibleNav.length) navigate(visibleNav[0].items[0].id)
                  }}
                />
              )}
              <button
                type="button"
                className="nav-link header-icon"
                title={searchOpen ? 'Fermer la recherche' : 'Rechercher un menu'}
                aria-label={searchOpen ? 'Fermer la recherche' : 'Rechercher un menu'}
                aria-expanded={searchOpen}
                onClick={() => {
                  if (searchOpen) {
                    setSearchOpen(false)
                    setMenuQuery('')
                  } else {
                    setSearchOpen(true)
                  }
                }}
              >
                <Icon name={searchOpen ? 'close' : 'search'} size={17} />
              </button>
            </li>
            <li className="nav-item">
              <button
                type="button"
                className="nav-link header-icon"
                title={theme === 'light' ? 'Activer le thème sombre' : 'Activer le thème clair'}
                aria-label={theme === 'light' ? 'Activer le thème sombre' : 'Activer le thème clair'}
                onClick={() => setTheme((previous) => (previous === 'light' ? 'dark' : 'light'))}
              >
                <Icon name={theme === 'light' ? 'moon' : 'sun'} size={17} />
              </button>
            </li>
            <li className="nav-item notifications" ref={notificationsRef}>
              <button
                type="button"
                className={`nav-link header-icon notification-btn ${notificationsOpen ? 'is-open' : ''}`}
                title="Notifications"
                aria-label="Notifications"
                aria-expanded={notificationsOpen}
                onClick={() => setNotificationsOpen((previous) => !previous)}
              >
                <Icon name="bell" size={17} />
              </button>
              {notificationsOpen && (
                <div className="notifications-panel" role="dialog" aria-label="Notifications récentes">
                  <div className="notifications-head">
                    <strong>Notifications</strong>
                    <span>{notifications.length} événement(s)</span>
                  </div>
                  <div className="notifications-list">
                    {notifications.length === 0 ? (
                      <div style={{ padding: '14px', fontSize: '11.5px', color: 'var(--text-muted)' }}>
                        Aucun incident ou alerte récente.
                      </div>
                    ) : notifications.map((event) => (
                      <button
                        type="button"
                        className="notification-item"
                        key={event.id}
                        onClick={() => {
                          notify(`${event.title} — ${event.detail}`, event.tone)
                          setNotificationsOpen(false)
                        }}
                      >
                        <span className={`notification-icon tone-${event.tone}`}>
                          <Icon name={event.icon} size={14} />
                        </span>
                        <span className="notification-body">
                          <strong>{event.title}</strong>
                          <small>{event.detail}</small>
                        </span>
                        <time>{event.time}</time>
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="notifications-footer"
                    onClick={() => { navigate('pilotage'); setNotificationsOpen(false) }}
                  >
                    Voir le journal d'activité
                  </button>
                </div>
              )}
            </li>
          </ul>
        </div>
      </header>

      <aside id="sidebar" className="menu-width sidebar bg-semi-dark">
        <nav aria-label="Navigation principale">
          <div className="custom-menu">
            <ul className="list-unstyled ps-0 root" id="menu">
              {visibleNav.map((group) => (
                <li key={group.label} className="menu-group">
                  <span className="menu-section-title">{group.label}</span>
                  <div className="menu-group-items">
                    {group.items.map((item) => {
                      const expanded = item.expandable && (parcExpanded || Boolean(normalizedQuery))
                      const isActive = activePage === item.id
                      return (
                        <div className="menu-item-wrap" key={item.id}>
                          <div className={`menu-link ${isActive ? 'active' : ''} ${item.expandable ? 'expandable' : ''}`}>
                            {item.expandable ? (
                              <button
                                type="button"
                                className="menu-toggle-row"
                                aria-expanded={expanded}
                                aria-controls="menu-buildings"
                                onClick={() => setParcExpanded((previous) => !previous)}
                              >
                                <Icon name={item.icon} size={15} />
                                <span>{item.label}</span>
                                <Icon name={expanded ? 'chevronDown' : 'chevronRight'} size={12} className="menu-chevron" />
                              </button>
                            ) : (
                              <a
                                href={routePath(item.id)}
                                aria-current={isActive ? 'page' : undefined}
                                onClick={(event) => { event.preventDefault(); navigate(item.id) }}
                              >
                                <Icon name={item.icon} size={15} />
                                <span>{item.label}</span>
                              </a>
                            )}
                          </div>

                          {item.expandable && expanded && (
                            <ul className="menu-children" id="menu-buildings">
                              {item.children.map((child) => {
                                const childActive = child.id === 'parc'
                                  ? activePage === 'parc' && !activeBuilding
                                  : Boolean(activeBuilding) && buildingSlug(activeBuilding) === child.id
                                return (
                                  <li className={`menu-child ${childActive ? 'active' : ''}`} key={child.id}>
                                    <a
                                      href={child.path}
                                      aria-current={childActive ? 'page' : undefined}
                                      onClick={(event) => {
                                        event.preventDefault()
                                        if (child.id === 'parc') {
                                          navigate('parc')
                                        } else {
                                          const building = buildings.find((entry) => buildingSlug(entry) === child.id)
                                          if (building) navigateBuilding(building)
                                        }
                                      }}
                                    >
                                      <Icon name={child.id === 'parc' ? 'monitor' : 'building'} size={11} />
                                      <span>{child.label}</span>
                                    </a>
                                  </li>
                                )
                              })}
                              <li className="menu-child menu-child-action">
                                <button type="button" onClick={() => { navigate('parc'); openBuildingModal() }}>
                                  <Icon name="plus" size={11} /> Ajouter un bâtiment
                                </button>
                              </li>
                            </ul>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </li>
              ))}
              {visibleNav.length === 0 && (
                <li className="menu-empty">Aucun menu ne correspond à « {menuQuery} ».</li>
              )}
            </ul>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-profile" ref={profileRef}>
            {profileOpen && (
              <div className="profile-menu" role="dialog" aria-label="Menu du compte">
                <div className="profile-menu-head">
                  <Avatar name={displayName} tone="brand" />
                  <span>
                    <strong>{displayName}</strong>
                    <small>{roleLabel} · session active</small>
                  </span>
                </div>
                <button
                  type="button"
                  className="profile-menu-item"
                  onClick={handleLogout}
                >
                  <Icon name="signOut" size={13} /> Se déconnecter
                </button>
              </div>
            )}
            <button
              type="button"
              className="sidebar-profile-btn"
              aria-expanded={profileOpen}
              aria-label="Compte administrateur"
              onClick={() => setProfileOpen((previous) => !previous)}
            >
              <Avatar name={displayName} tone="brand" />
              <span className="sidebar-profile-identity">
                <strong>{displayName}</strong>
                <small><span className="status-dot online" /> {roleLabel}</small>
              </span>
              <Icon name={profileOpen ? 'chevronUp' : 'chevronDown'} size={12} className="menu-chevron" />
            </button>
          </div>
          <span className="version">LyuX Admin · {setupStatus?.school_year || '2026 – 2027'}</span>
        </div>
      </aside>

      <main id="main" className="p-3">
        <div id="pjax-container">
          <section className="content">
            {!canAccessActivePage ? (
              <div className="card" style={{ padding: 24 }}>
                <h3 style={{ marginTop: 0 }}>Accès restreint</h3>
                <p className="muted">Votre rôle effectif ({roleLabel}) ne dispose pas de la permission requise pour cette section.</p>
                <button type="button" className="btn btn-primary btn-sm" onClick={() => navigate('dashboard')}>
                  Retour au tableau de bord
                </button>
              </div>
            ) : route.page === 'parc' && route.room ? (
              <ParcSalle
                building={activeBuilding}
                room={activeRoom}
                buildingSlug={route.child}
                roomSlug={route.room}
                notify={notify}
                navigate={navigate}
                navigateBuilding={navigateBuilding}
                permissions={userPerms || {}}
              />
            ) : (route.page === 'parc' && route.child ? (
              <ParcBatiment
                building={activeBuilding}
                buildingSlug={route.child}
                notify={notify}
                navigate={navigate}
                onCreateBuilding={openBuildingModal}
                onOpenRoom={(room) => navigateRoom(activeBuilding, room)}
                permissions={userPerms || {}}
              />
            ) : (
              <ActivePage
                notify={notify}
                navigate={navigate}
                navigateBuilding={navigateBuilding}
                navigateRoom={navigateRoom}
                buildings={buildings}
                onCreateBuilding={openBuildingModal}
                currentUser={user}
                permissions={userPerms || {}}
                onSetupSaved={(nextSetup) => {
                  setSetupStatus(nextSetup)
                  refreshServerData()
                }}
              />
            ))}
            <footer className="page-footer">
              <span>LyuX Administration</span>
              <span>Opération Manchot 2026</span>
            </footer>
          </section>
        </div>
      </main>

      <BuildingModal
        open={buildingModalOpen}
        name={newBuildingName}
        onNameChange={setNewBuildingName}
        onClose={() => setBuildingModalOpen(false)}
        onCreate={createBuilding}
      />

      <div className="toast-stack" aria-live="polite">
        {toasts.map((toast) => (
          <div className={`toast lyux-toast tone-${toast.tone}`} key={toast.id}>
            <Icon name={toast.tone === 'warning' ? 'alert' : toast.tone === 'info' ? 'info' : 'checkCircle'} size={17} />
            <span>{toast.message}</span>
            <button type="button" aria-label="Fermer la notification" onClick={() => setToasts((previous) => previous.filter((item) => item.id !== toast.id))}>
              <Icon name="close" size={13} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
