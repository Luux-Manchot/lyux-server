import React from 'react'

// Le prototype utilise directement la feuille d'icônes Font Awesome fournie par
// Open Admin (`icon-*`, cf. vendor/open-admin/css/styles.css). Aucune dépendance
// supémentaire, aucun emoji : on conserve uniquement les noms logiques LyuX et
// on les traduit vers les classes réelles du panneau.
const ICON_CLASSES = {
  dashboard: 'tachometer-alt',
  building: 'building',
  monitor: 'desktop',
  server: 'server',
  book: 'book',
  users: 'users',
  shield: 'shield-alt',
  puzzle: 'puzzle-piece',
  settings: 'cog',
  search: 'search',
  plus: 'plus',
  chevronDown: 'chevron-down',
  chevronUp: 'chevron-up',
  chevronRight: 'chevron-right',
  chevronLeft: 'chevron-left',
  arrowLeft: 'arrow-left',
  signOut: 'sign-out-alt',
  arrowUpRight: 'external-link-alt',
  bell: 'bell',
  menu: 'bars',
  sun: 'sun',
  moon: 'moon',
  refresh: 'sync',
  zap: 'bolt',
  trash: 'trash',
  pencil: 'pen',
  eye: 'eye',
  more: 'ellipsis-h',
  close: 'times',
  check: 'check',
  alert: 'exclamation-triangle',
  checkCircle: 'check-circle',
  info: 'info-circle',
  download: 'download',
  send: 'paper-plane',
  lock: 'lock',
  unlock: 'unlock',
  key: 'key',
  folder: 'folder',
  boxes: 'boxes',
  network: 'project-diagram',
  activity: 'heartbeat',
  clock: 'clock',
  calendar: 'calendar',
  file: 'file',
  graduation: 'graduation-cap',
  briefcase: 'briefcase',
  layers: 'layers',
  filter: 'filter',
  save: 'save',
  external: 'external-link-alt',
  power: 'power-off',
  wifi: 'wifi',
  package: 'box',
  globe: 'globe',
  database: 'database',
  circle: 'circle',
}

export function Icon({ name, size = 16, className = '', ...rest }) {
  return (
    <i
      className={`fas icon-${ICON_CLASSES[name] || ICON_CLASSES.circle} ${className}`.trim()}
      style={{ fontSize: `${size}px`, lineHeight: 1 }}
      aria-hidden="true"
      {...rest}
    />
  )
}

export default Icon
