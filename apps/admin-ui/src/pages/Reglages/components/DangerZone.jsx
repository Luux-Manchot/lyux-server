import React from 'react'
import { Button, Card } from '../../../components.jsx'
import { api } from '../../../api/client.js'

export default function DangerZone({ notify }) {
  const handleReset = async () => {
    try {
      await api.saveSettings({ enrollment_enabled: true, auto_update_clients: true })
      notify('Paramètres serveur réinitialisés aux valeurs par défaut.', 'warning')
    } catch (err) {
      notify(err.message || 'Erreur lors de la réinitialisation.', 'danger')
    }
  }

  return (
    <Card title="Zone sensible" subtitle="Opérations critiques sur la configuration serveur">
      <div className="danger-zone">
        <Button variant="danger" icon="refresh" onClick={handleReset}>Réinitialiser les paramètres serveur</Button>
      </div>
    </Card>
  )
}
