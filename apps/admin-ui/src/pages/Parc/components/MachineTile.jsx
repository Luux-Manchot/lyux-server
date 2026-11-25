import React from 'react'
import { Badge } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function MachineTile({ machine, selected, onClick }) {
  return (
    <button
      type="button"
      className={`pc-tile ${selected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <span className={`pc-status ${machine.status}`}><Icon name="monitor" size={22} /></span>
      <strong>{machine.hostname}</strong>
      <small>{machine.ip}</small>
      <Badge tone={machine.status === 'online' ? 'success' : 'neutral'} dot>
        {machine.status === 'online' ? 'En ligne' : 'Hors ligne'}
      </Badge>
    </button>
  )
}
