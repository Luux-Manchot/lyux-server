import React from 'react'
import { Card } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

const ACTIONS = [
  { label: 'Bâtiments & salles', icon: 'building', page: 'parc' },
  { label: 'Postes & Mises à jour', icon: 'monitor', page: 'pilotage' },
  { label: 'Catalogue logiciels', icon: 'layers', page: 'logiciels' },
  { label: 'Comptes & Classes', icon: 'users', page: 'utilisateurs' },
]

export default function QuickActions({ navigate }) {
  return (
    <Card title="Actions rapides" subtitle="Accès direct aux opérations courantes">
      <div className="quick-actions">
        {ACTIONS.map((action) => (
          <button type="button" className="quick-action" key={action.page} onClick={() => navigate(action.page)}>
            <span className="quick-icon"><Icon name={action.icon} size={19} /></span>
            <span>{action.label}</span>
            <Icon name="arrowUpRight" size={15} />
          </button>
        ))}
      </div>
    </Card>
  )
}
