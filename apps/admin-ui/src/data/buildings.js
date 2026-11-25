// Bâtiments du prototype : la liste initiale vient du jeu de données simulé,
// mais elle peut grandir pendant la session (ajout depuis la sidebar ou la page Parc).
import { buildings as mockBuildings } from './mock.js'

export const initialBuildings = () => mockBuildings.map((building) => ({ ...building }))

export function buildingSlug(building) {
  const source = building?.id || building?.name || ''
  return source
    .toString()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

// Cherche le premier identifiant libre (BAT-H, BAT-I, …) puis tombe sur un
// numéro si toutes les lettres sont utilisées : la liste n'est jamais figée.
export function nextBuildingId(list) {
  const used = new Set(list.map((building) => building.id))
  for (let index = 0; index < 26; index += 1) {
    const candidate = `BAT-${String.fromCharCode(65 + index)}`
    if (!used.has(candidate)) return candidate
  }
  let suffix = list.length + 1
  while (used.has(`BAT-${suffix}`)) suffix += 1
  return `BAT-${suffix}`
}
