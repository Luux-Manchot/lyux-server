import React from 'react'
import { Card, SettingRow, Toggle } from '../../../components.jsx'
import ServerBuildCard from './ServerBuildCard.jsx'

export default function UpdatesTab({ form, set }) {
  return (
    <>
      <Card title="Politique de mise à jour" subtitle="Comportement du parc client">
        <SettingRow
          icon="download"
          title="Mises à jour automatiques"
          description="Diffuser automatiquement les nouvelles versions disponibles."
          control={<Toggle checked={form.autoUpdate} onChange={set('autoUpdate')} label="Mises à jour automatiques" />}
        />
        <SettingRow
          icon="clock"
          title="Fenêtre de déploiement"
          description="Plage horaire pendant laquelle les mises à jour sont appliquées."
          control={<input className="compact-input" value={form.updateWindow} onChange={(event) => set('updateWindow')(event.target.value)} />}
        />
        <SettingRow
          icon="database"
          title="Conservation des journaux"
          description="Nombre de jours pendant lesquels les journaux sont conservés."
          control={<input className="compact-input small" type="number" value={form.retention} onChange={(event) => set('retention')(Number(event.target.value))} />}
        />
      </Card>
      <ServerBuildCard />
    </>
  )
}
