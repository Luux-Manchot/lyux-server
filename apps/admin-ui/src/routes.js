// Routage History API du prototype. Toutes les URLs (bâtiments et salles)
// passent par ces helpers pour rester valides si le prototype est servi sous
// un sous-chemin.
import { buildingSlug } from './data/buildings.js'

export const BASE = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')

export function routePath(page) {
  return `${BASE}/${page}/`
}

export function buildingPath(building) {
  return `${BASE}/parc/${buildingSlug(building)}/`
}

export function roomSlug(room) {
  return (room?.id || '')
    .toString()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function roomPath(building, room) {
  return `${BASE}/parc/${buildingSlug(building)}/${roomSlug(room)}/`
}

export function readRoute() {
  const baseSegments = BASE.split('/').filter(Boolean).length
  const segments = window.location.pathname.split('/').filter(Boolean)
  return {
    page: segments[baseSegments] || 'dashboard',
    child: segments[baseSegments + 1] || null,
    room: segments[baseSegments + 2] || null,
  }
}

export function pushRoute(page, child = null, room = null) {
  const parts = [BASE, page, child, room].filter(Boolean)
  // BASE peut être vide (racine du serveur de dev) : on remet explicitement le
  // « / » initial, sinon pushState résout une URL relative au chemin courant.
  const path = `/${parts.join('/')}/`
  if (window.location.pathname !== path) {
    window.history.pushState({ page, child, room }, '', path)
  }
}
