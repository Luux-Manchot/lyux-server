import React from 'react'
import { Card } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function IntegrationNote() {
  return (
    <Card title="Principe d'intégration" subtitle="Architecture retenue pour le panneau">
      <div className="note-box">
        <Icon name="info" size={18} />
        <p>
          La console système <strong>Cockpit</strong> reste l'outil de référence pour l'administration bas niveau.
          Le nouveau panneau est une interface autonome qui s'appuie sur les services déjà présents, sans les remplacer.
          Les services sont supervisés en direct via l’API LyuX (`/api/v1/integrations/status`).
        </p>
      </div>
    </Card>
  )
}
