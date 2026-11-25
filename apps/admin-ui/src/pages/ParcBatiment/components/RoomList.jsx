import React from 'react'
import { Badge, Card, EmptyState, Toolbar } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

const PROFILE_LABELS = {
  nsi: 'NSI / Développement',
  standard: 'Standard',
  sciences: 'Sciences',
  multimedia: 'Multimédia',
  atelier: 'Atelier',
}

function roomStatus(roomId, machines) {
  const list = machines.filter((machine) => machine.room === roomId)
  if (!list.length) return { label: 'Sans poste', tone: 'neutral' }
  const online = list.filter((machine) => machine.status === 'online').length
  if (online === list.length) return { label: 'Opérationnel', tone: 'success' }
  if (online > 0) return { label: 'Partiel', tone: 'warning' }
  return { label: 'Arrêté', tone: 'neutral' }
}

export default function RoomList({ building, rooms, machines, search, onSearch, onOpenRoom }) {
  const term = search.trim().toLowerCase()
  const visibleRooms = rooms.filter((room) => !term
    || room.id.toLowerCase().includes(term)
    || PROFILE_LABELS[room.profile]?.toLowerCase().includes(term))

  return (
    <Card
      title={`Salles · ${building.name}`}
      subtitle="Une carte par salle, avec son état et ses postes"
    >
      <Toolbar
        search={search}
        onSearch={onSearch}
        placeholder="Rechercher une salle…"
      />

      {visibleRooms.length === 0 ? (
        <EmptyState
          icon="search"
          title="Aucune salle"
          description="Aucune salle dans ce bâtiment pour le moment."
          compact
        />
      ) : (
        <div className="room-cards">
          {visibleRooms.map((room) => {
            const roomMachines = machines.filter((machine) => machine.room === room.id)
            const updates = roomMachines.filter((machine) => machine.updates > 0).length
            const status = roomStatus(room.id, machines)
            return (
              <button
                type="button"
                className="room-card"
                key={room.id}
                onClick={() => onOpenRoom(room)}
              >
                <span className="room-card-head">
                  <span className="room-card-icon"><Icon name="monitor" size={17} /></span>
                  <strong>Salle {room.id}</strong>
                  <Badge tone={status.tone} dot>{status.label}</Badge>
                </span>
                <span className="room-card-profile">{PROFILE_LABELS[room.profile] || room.profile}</span>
                <span className="room-card-foot">
                  <span><Icon name="desktop" size={12} /> {roomMachines.length} / {room.capacity} postes</span>
                  {updates > 0 && (
                    <span className="room-card-updates">
                      <Icon name="download" size={11} /> {updates} màj
                    </span>
                  )}
                </span>
              </button>
            )
          })}
        </div>
      )}
    </Card>
  )
}
