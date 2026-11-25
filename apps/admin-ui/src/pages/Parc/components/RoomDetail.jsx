import React from 'react'
import { Button, Card } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'
import MachineDetail from './MachineDetail.jsx'
import MachineTile from './MachineTile.jsx'
import { PROFILE_LABELS, buildingName } from './utils.js'

export default function RoomDetail({
  room,
  machines,
  buildings = [],
  selectedBuilding,
  selectedMachine,
  onSelectMachine,
  onBack,
  onWakeRoom,
  onDelete,
  onWakeMachine,
  onMoveMachine,
  onRemoveMachine,
}) {
  return (
    <>
      <button type="button" className="back-link" onClick={onBack}>
        <Icon name="arrowLeft" size={15} /> Toutes les salles de {buildingName(selectedBuilding, buildings)}
      </button>

      <Card
        title={`Salle ${room.id}`}
        subtitle={`${PROFILE_LABELS[room.profile]} · capacité ${room.capacity} postes`}
        actions={
          <>
            <Button icon="zap" onClick={onWakeRoom}>
              Réveiller la salle
            </Button>
            <Button variant="danger" icon="trash" onClick={onDelete}>
              Supprimer
            </Button>
          </>
        }
      >
        <div className="room-layout">
          <div>
            <div className="subheading">Postes de la salle</div>
            <div className="pc-grid">
              {machines.map((machine) => (
                <MachineTile
                  key={machine.id}
                  machine={machine}
                  selected={selectedMachine?.id === machine.id}
                  onClick={() => onSelectMachine(machine)}
                />
              ))}
              {machines.length === 0 && <p className="muted">Aucun poste assigné à cette salle.</p>}
            </div>
          </div>

          <MachineDetail
            machine={selectedMachine}
            onWake={onWakeMachine}
            onMove={onMoveMachine}
            onRemove={onRemoveMachine}
          />
        </div>
      </Card>
    </>
  )
}
