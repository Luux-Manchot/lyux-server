import React from 'react'
import { Badge, Card, KeyValue } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

const PROFILE_LABELS = {
  nsi: 'NSI / Développement',
  standard: 'Standard',
  sciences: 'Sciences',
  multimedia: 'Multimédia',
  atelier: 'Atelier',
}

export function roomStatus(machines) {
  if (!machines.length) return { label: 'Sans poste', tone: 'neutral' }
  const online = machines.filter((machine) => machine.status === 'online').length
  if (online === machines.length) return { label: 'Opérationnel', tone: 'success' }
  if (online > 0) return { label: 'Partiel', tone: 'warning' }
  return { label: 'Arrêté', tone: 'neutral' }
}

export default function RoomInfo({ building, room, machines }) {
  const status = roomStatus(machines)
  const updates = machines.filter((machine) => machine.updates > 0).length

  return (
    <Card title={`Informations · ${room.id}`} subtitle="Configuration de la salle et suivi du parc">
      <div className="room-info-grid">
        <KeyValue label="Bâtiment" value={building?.name || room.buildingId} />
        <KeyValue label="Profil" value={PROFILE_LABELS[room.profile] || room.profile} />
        <KeyValue label="Capacité" value={`${room.capacity} postes`} />
        <KeyValue label="Postes inventoriés" value={`${machines.length} / ${room.capacity}`} />
        <KeyValue
          label="État de la salle"
          value={<Badge tone={status.tone} dot>{status.label}</Badge>}
        />
        <KeyValue
          label="Mises à jour"
          value={updates > 0
            ? <Badge tone="warning"><Icon name="download" size={12} /> {updates} postes à traiter</Badge>
            : <Badge tone="success" dot>À jour</Badge>}
        />
      </div>
    </Card>
  )
}
