import React from 'react'
import { Badge, Card, DataTable, IconButton, Select, Toggle, Toolbar } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'
import { PROFILE_LABELS, buildingName, statusOf } from './utils.js'

export default function RoomsTable({
  rooms,
  buildings,
  machines,
  selectedBuilding,
  search,
  onSearch,
  onBuildingChange,
  enrollment,
  onEnrollmentChange,
  onOpenRoom,
  onEditRoom,
  onDeleteRoom,
}) {
  return (
    <Card
      title={`Salles · ${buildingName(selectedBuilding, buildings)}`}
      subtitle={buildings.find((building) => building.id === selectedBuilding)?.description}
      actions={
        <div className="inline-toggle">
          <span>Enrôlement des postes</span>
          <Toggle checked={enrollment} onChange={onEnrollmentChange} label="Enrôlement des postes" />
          <Badge tone={enrollment ? 'success' : 'neutral'} dot>{enrollment ? 'Actif' : 'Désactivé'}</Badge>
        </div>
      }
    >
      <Toolbar
        search={search}
        onSearch={onSearch}
        placeholder="Rechercher une salle ou un poste…"
        filters={
          <Select
            label="Bâtiment"
            value={selectedBuilding}
            onChange={onBuildingChange}
            options={buildings.map((building) => ({ value: building.id, label: building.name }))}
          />
        }
      />
      <DataTable
        columns={[
          {
            key: 'id',
            label: 'Salle',
            render: (room) => (
              <button type="button" className="link-like" onClick={() => onOpenRoom(room)}>
                <Icon name="monitor" size={15} /> {room.id}
              </button>
            ),
          },
          { key: 'building', label: 'Bâtiment', render: (room) => buildingName(room.buildingId, buildings) },
          { key: 'profile', label: 'Profil', render: (room) => <Badge tone="brand">{PROFILE_LABELS[room.profile]}</Badge> },
          { key: 'capacity', label: 'Postes configurés', render: (room) => <strong>{machines.filter((m) => m.room === room.id).length} / {room.capacity}</strong> },
          { key: 'status', label: 'État du parc', render: (room) => <Badge tone={statusOf(room.id).tone} dot>{statusOf(room.id).label}</Badge> },
          {
            key: 'actions',
            label: 'Actions',
            align: 'right',
            render: (room) => (
              <div className="row-actions">
                <IconButton icon="eye" label={`Voir ${room.id}`} onClick={() => onOpenRoom(room)} />
                <IconButton icon="pencil" label={`Modifier ${room.id}`} onClick={() => onEditRoom(room)} />
                <IconButton icon="trash" label={`Supprimer ${room.id}`} onClick={() => onDeleteRoom(room)} />
              </div>
            ),
          },
        ]}
        rows={rooms}
        onRowClick={onOpenRoom}
      />
    </Card>
  )
}
