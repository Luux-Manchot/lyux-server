import React, { useEffect, useState } from 'react'
import { Badge, Card, EmptyState } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'
import MachineInfo from './MachineInfo.jsx'

// Les postes sont sélectionnables : aucun bouton d'action dans une carte.
// Le détail s'affiche dans le panneau de droite (MachineInfo).
export default function MachineCards({ building, room, machines }) {
  const [selectedId, setSelectedId] = useState(machines[0]?.id || null)

  // Quand on change de salle via l'URL, on sélectionne le premier poste de la nouvelle salle.
  useEffect(() => {
    setSelectedId(machines[0]?.id || null)
  }, [room?.id])

  const selectedMachine = machines.find((machine) => machine.id === selectedId) || null

  return (
    <Card
      title="Postes de la salle"
      subtitle="Sélectionnez un poste pour consulter ses informations"
    >
      {machines.length === 0 ? (
        <EmptyState
          icon="monitor"
          title="Aucun poste"
          description="Aucun poste n'est rattaché à cette salle."
          compact
        />
      ) : (
        <div className="room-machines-layout">
          <div className="machine-picker" role="listbox" aria-label="Postes de la salle">
            {machines.map((machine) => {
              const online = machine.status === 'online'
              const isSelected = machine.id === selectedId
              return (
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`machine-card ${isSelected ? 'selected' : ''}`}
                  key={machine.id}
                  onClick={() => setSelectedId(machine.id)}
                >
                  <span className="machine-card-head">
                    <span className={`machine-icon ${machine.status}`}>
                      <Icon name="monitor" size={16} />
                    </span>
                    <strong>{machine.hostname}</strong>
                    {isSelected && <Icon name="check" size={13} className="machine-card-check" />}
                  </span>
                  <span className="machine-card-meta">
                    <span>{machine.ip}</span>
                    <Badge tone={online ? 'success' : 'neutral'} dot>
                      {online ? 'En ligne' : 'Hors ligne'}
                    </Badge>
                  </span>
                  <span className="machine-card-foot">
                    <span><Icon name="clock" size={11} /> {machine.lastSeen || '—'}</span>
                    {machine.updates > 0 && <Badge tone="warning">{machine.updates} màj</Badge>}
                  </span>
                </button>
              )
            })}
          </div>

          <MachineInfo machine={selectedMachine} building={building} />
        </div>
      )}
    </Card>
  )
}
