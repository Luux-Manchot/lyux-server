import React from 'react'
import { Badge, Button, Card, IconButton, Toggle } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

const ICON_BY_CATEGORY = {
  Identité: 'shield',
  Supervision: 'activity',
  Inventaire: 'file',
  Système: 'server',
  Interface: 'globe',
  Infrastructure: 'database',
}

const SERVICE_PORTS = {
  glpi: 8085,
  kuma: 3001,
  hub: 8086,
  'admin-ui': 8087,
  proxy: 3142,
}

export default function IntegrationCard({ item, enabled, onToggle, notify }) {
  const port = SERVICE_PORTS[item.id]
  const handleOpen = () => {
    if (port && typeof window !== 'undefined') {
      window.open(`${window.location.protocol}//${window.location.hostname}:${port}`, '_blank', 'noopener')
      return
    }
    notify(`${item.name} : ${item.detail}`, 'info')
  }
  return (
    <Card
      className="integration-card"
      title={
        <span className="integration-title">
          <span className="integration-icon"><Icon name={ICON_BY_CATEGORY[item.category] || 'puzzle'} size={19} /></span>
          {item.name}
        </span>
      }
      subtitle={item.category}
      actions={<Badge tone={item.status === 'active' ? 'success' : 'warning'} dot>{item.status === 'active' ? 'Actif' : 'Prévu'}</Badge>}
    >
      <p className="integration-description">{item.description}</p>
      <div className="integration-detail"><Icon name="info" size={13} /> {item.detail}</div>
      <div className="integration-footer">
        <div className="inline-toggle">
          <span>Activé</span>
          <Toggle
            checked={enabled}
            onChange={onToggle}
            label={`Activer ${item.name}`}
          />
        </div>
        <div className="row-actions">
          <Button size="sm" icon="external" onClick={handleOpen}>Ouvrir</Button>
        </div>
      </div>
    </Card>
  )
}
