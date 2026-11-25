import React from 'react'
import { Card, SettingRow, Toggle } from '../../../components.jsx'
import { api } from '../../../api/client.js'
import DangerZone from './DangerZone.jsx'

export default function SecurityTab({ form, set, notify, maintenance, setMaintenance }) {
  const handleMaintenance = async (value) => {
    setMaintenance(value)
    try {
      await api.saveSettings({ maintenance_mode: value })
      notify(value ? 'Mode maintenance activé.' : 'Mode maintenance désactivé.', value ? 'warning' : 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors du changement de mode.', 'danger')
    }
  }
  return (
    <>
      <Card title="Sessions & accès" subtitle="Règles appliquées à tous les comptes">
        <SettingRow
          icon="clock"
          title="Expiration des sessions"
          description="Durée d'inactivité avant déconnexion automatique (minutes)."
          control={<input className="compact-input small" type="number" value={form.sessionTimeout} onChange={(event) => set('sessionTimeout')(Number(event.target.value))} />}
        />
        <SettingRow
          icon="shield"
          title="Enrôlement des postes"
          description="Autoriser les nouveaux postes à rejoindre le parc automatiquement."
          control={<Toggle checked={form.enrollment} onChange={set('enrollment')} label="Enrôlement des postes" />}
        />
        <SettingRow
          icon="power"
          title="Mode maintenance"
          description="Suspend temporairement l'accès au panneau aux utilisateurs non administrateurs."
          control={<Toggle checked={maintenance} onChange={handleMaintenance} label="Mode maintenance" />}
        />
      </Card>
      <DangerZone notify={notify} />
    </>
  )
}
