import React from 'react'
import { Card } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function DeploymentHistory() {
  return (
    <Card title="Historique des déploiements" subtitle="Journal des opérations de distribution">
      <div className="note-box" style={{ marginTop: 0 }}>
        <Icon name="info" size={16} />
        <p>Aucun historique enregistré pour le moment. Le suivi détaillé des déploiements sera connecté dès qu’un journal persistant sera activé sur l’API.</p>
      </div>
    </Card>
  )
}
