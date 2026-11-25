import React from 'react'
import { Card } from '../../../components.jsx'

// Couleurs de référence : voir docs/admin-ui-couleurs-etats.md.
export default function BuildingDistribution({ buildings, machines, rooms }) {
  const buildingOf = (roomId) => rooms.find((room) => room.id === roomId)?.buildingId

  return (
    <Card title="Répartition du parc" subtitle="État des postes et mises à jour par bâtiment">
      <div className="building-legend" aria-label="Légende des couleurs">
        <span><i className="legend-dot online" /> En ligne</span>
        <span><i className="legend-dot offline" /> Hors ligne</span>
        <span><i className="legend-dot updates" /> Mises à jour en attente</span>
      </div>

      <div className="building-bars">
        {buildings.map((building) => {
          const posts = machines.filter((machine) => buildingOf(machine.room) === building.id)
          const online = posts.filter((machine) => machine.status === 'online').length
          const offline = posts.length - online
          const updates = posts.filter((machine) => machine.updates > 0).length
          const onlinePct = posts.length ? Math.round((online / posts.length) * 100) : 0
          const offlinePct = posts.length ? Math.round((offline / posts.length) * 100) : 0

          return (
            <div className="building-bar detailed" key={building.id}>
              <span className="bar-label">{building.name}</span>
              <div
                className="building-status-track"
                role="img"
                aria-label={`${online} en ligne, ${offline} hors ligne sur ${posts.length} ${posts.length > 1 ? 'postes' : 'poste'}`}
              >
                <span className="building-status-segment online" style={{ width: `${onlinePct}%` }} />
                <span className="building-status-segment offline" style={{ width: `${offlinePct}%` }} />
              </div>
              <span className="building-status-counts">
                <span className="status-count online" title="Postes en ligne">{online}</span>
                <span className="status-count offline" title="Postes hors ligne">{offline}</span>
                <span className="status-count updates" title="Postes avec des mises à jour en attente">{updates} màj</span>
              </span>
            </div>
          )
        })}
      </div>

      <p className="building-note">
        Les postes avec mise à jour peuvent aussi être éteints : leur compte est affiché à part.
      </p>
    </Card>
  )
}
