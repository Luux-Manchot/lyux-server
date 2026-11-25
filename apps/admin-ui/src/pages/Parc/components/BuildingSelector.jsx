import React from 'react'
import { Card, IconButton } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function BuildingSelector({ buildings, rooms, selectedBuilding, onSelectBuilding, onDelete }) {
  return (
    <Card padded={false}>
      <div className="building-selector">
        <div className="building-selector-label"><Icon name="building" size={16} /> Bâtiments</div>
        <div className="building-pills">
          {buildings.map((building) => (
            <button
              type="button"
              key={building.id}
              className={`building-pill ${selectedBuilding === building.id ? 'active' : ''}`}
              onClick={() => onSelectBuilding(building.id)}
            >
              {building.name}
              <span>{rooms.filter((room) => room.buildingId === building.id).length}</span>
            </button>
          ))}
        </div>
        <IconButton icon="trash" label="Supprimer le bâtiment sélectionné" onClick={onDelete} />
      </div>
    </Card>
  )
}
