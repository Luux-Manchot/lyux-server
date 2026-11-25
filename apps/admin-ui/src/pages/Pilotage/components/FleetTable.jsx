import React from 'react'
import { Badge, Button, Card, DataTable, Toggle, Toolbar } from '../../../components.jsx'
import { api } from '../../../api/client.js'

export default function FleetTable({ notify, search, onSearch, autoUpdate, onAutoUpdateChange, rows }) {
  const handleUpdateMachine = async (machine) => {
    try {
      await api.applyUpdates()
      notify(`Ordre de mise à jour envoyé pour ${machine.hostname}.`, 'success')
    } catch (err) {
      notify(err.message || `Impossible de mettre à jour ${machine.hostname}.`, 'danger')
    }
  }
  return (
    <Card
      title="État détaillé du parc"
      subtitle="Versions et disponibilité des postes clients"
      actions={
        <div className="inline-toggle">
          <span>Mises à jour automatiques</span>
          <Toggle checked={autoUpdate} onChange={onAutoUpdateChange} label="Mises à jour automatiques" />
        </div>
      }
    >
      <Toolbar search={search} onSearch={onSearch} placeholder="Rechercher un poste ou une adresse IP…" />
      <DataTable
        columns={[
          { key: 'hostname', label: 'Poste', render: (machine) => <strong>{machine.hostname}</strong> },
          { key: 'location', label: 'Bâtiment / salle', render: (machine) => `${machine.building_id || machine.buildingId || '—'} / ${machine.room || '—'}` },
          { key: 'ip', label: 'Adresse IP', render: (machine) => <span className="mono">{machine.ip}</span> },
          { key: 'version', label: 'Version', render: (machine) => <span className="mono">{machine.version}</span> },
          { key: 'build', label: 'Build', render: (machine) => <span className="mono muted">{machine.build}</span> },
          { key: 'network', label: 'État réseau', render: (machine) => <Badge tone={machine.status === 'online' ? 'success' : 'neutral'} dot>{machine.status === 'online' ? 'En ligne' : 'Hors ligne'}</Badge> },
          { key: 'update', label: 'Statut version', render: (machine) => <Badge tone={machine.updates === 0 ? 'success' : 'warning'}>{machine.updates === 0 ? 'À jour' : `${machine.updates} paquets`}</Badge> },
          {
            key: 'actions',
            label: 'Actions',
            align: 'right',
            render: (machine) => (
              <Button size="sm" icon="download" onClick={() => handleUpdateMachine(machine)}>
                Mettre à jour
              </Button>
            ),
          },
        ]}
        rows={rows}
      />
    </Card>
  )
}
