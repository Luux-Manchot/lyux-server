export const initialBuildings = () => []

export const buildingSlug = (name) =>
  String(name || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')

export const nextBuildingId = (buildings = []) => {
  const used = new Set((buildings || []).map((b) => String(b.id || '').toUpperCase()))
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  for (const ch of letters) {
    const candidate = `BAT-${ch}`
    if (!used.has(candidate)) return candidate
  }
  return `BAT-${(buildings?.length || 0) + 1}`
}
