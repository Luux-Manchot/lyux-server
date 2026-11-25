export const PROFILE_LABELS = {
  'global-socle': 'Socle global lycée',
  nsi: 'NSI / Développement',
  standard: 'Standard',
  sciences: 'Sciences',
  multimedia: 'Multimédia',
  atelier: 'Atelier',
}

export const buildingName = (id, buildings = []) => (
  buildings.find((building) => building.id === id)?.name || id
)

export const statusOf = (roomId, machines = []) => {
  const list = machines.filter((machine) => machine.room === roomId)
  const online = list.filter((machine) => machine.status === 'online').length
  if (online === list.length && list.length > 0) return { label: 'Opérationnel', tone: 'success' }
  if (online > 0) return { label: 'Partiel', tone: 'warning' }
  return { label: 'Arrêté', tone: 'neutral' }
}
