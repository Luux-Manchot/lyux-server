import React, { useEffect, useState } from 'react'
import { Badge, Button, Card, IconButton, PageActions, Toggle, Toolbar } from '../../components.jsx'
import { Icon } from '../../icons.jsx'
import { api } from '../../api/client.js'
import RoomModal from './components/RoomModal.jsx'
import './Parc.css'

export default function Parc({ notify, buildings, onCreateBuilding, navigateBuilding }) {
  const [rooms, setRooms] = useState([])
  const [machines, setMachines] = useState([])
  const [selectedBuilding, setSelectedBuilding] = useState('BAT-C')
  const [search, setSearch] = useState('')
  const [enrollment, setEnrollment] = useState(true)
  const [showRoomModal, setShowRoomModal] = useState(false)
  const [newRoomName, setNewRoomName] = useState('')

  useEffect(() => {
    api.getRooms()
      .then((list) => {
        if (Array.isArray(list) && list.length > 0) {
          setRooms(list.map((r) => ({
            ...r,
            buildingId: r.building_id || r.buildingId,
          })))
        }
      })
      .catch(() => {})
    api.getMachines()
      .then((list) => {
        if (Array.isArray(list) && list.length > 0) setMachines(list)
      })
      .catch(() => {})
    api.getSettings()
      .then((res) => {
        if (typeof res?.enrollment_enabled === 'boolean') {
          setEnrollment(res.enrollment_enabled)
        }
      })
      .catch(() => {})
  }, [])

  const handleToggleEnrollment = async (nextValue) => {
    const prev = enrollment
    setEnrollment(nextValue)
    try {
      await api.saveSettings({ enrollment_enabled: nextValue })
      notify(nextValue ? 'Enrôlement des postes activé.' : 'Enrôlement des postes désactivé.', nextValue ? 'success' : 'warning')
    } catch (err) {
      setEnrollment(prev)
      notify(err.message || 'Impossible de modifier l’état de l’enrôlement.', 'danger')
    }
  }

  // Si le bâtiment sélectionné disparaît (ou au premier chargement), on retombe
  // sur le premier de la liste partagée.
  useEffect(() => {
    if (!buildings.some((building) => building.id === selectedBuilding)) {
      setSelectedBuilding(buildings[0]?.id || '')
    }
  }, [buildings, selectedBuilding])

  const selectBuilding = (id) => {
    const target = buildings.find((b) => b.id === id)
    if (target && navigateBuilding) {
      navigateBuilding(target)
      return
    }
    setSelectedBuilding(id)
  }

  const createRoom = async () => {
    const id = newRoomName.trim().toUpperCase()
    if (!id) {
      notify('Saisissez un nom de salle.', 'warning')
      return
    }
    try {
      const res = await api.createRoom({
        id,
        name: id,
        building_id: selectedBuilding,
        profile: 'standard',
        capacity: 24,
        teacher: '',
      })
      const created = res?.room || { id, buildingId: selectedBuilding, profile: 'standard', capacity: 24, teacher: '' }
      setRooms((prev) => [...prev, { ...created, buildingId: created.building_id || selectedBuilding }])
      setShowRoomModal(false)
      setNewRoomName('')
      notify(`Salle ${id} créée.`, 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors de la création de la salle.', 'danger')
    }
  }

  const buildingStats = (buildingId) => {
    const bRooms = rooms.filter((r) => r.buildingId === buildingId)
    const roomIds = new Set(bRooms.map((r) => r.id))
    const bMachines = machines.filter((m) => roomIds.has(m.room))
    const offline = bMachines.filter((m) => m.status !== 'online').length
    const pendingUpdates = bMachines.filter((m) => (m.updates || 0) > 0).length
    const issues = offline + pendingUpdates
    return {
      roomsCount: bRooms.length,
      machinesCount: bMachines.length,
      onlineCount: bMachines.length - offline,
      offlineCount: offline,
      pendingUpdates,
      issues,
    }
  }

  const visibleBuildings = buildings.filter((b) => {
    const term = search.trim().toLowerCase()
    if (!term) return true
    return (
      b.name.toLowerCase().includes(term) ||
      b.id.toLowerCase().includes(term) ||
      (b.description || '').toLowerCase().includes(term)
    )
  })

  return (
    <>
      <PageActions>
        <div className="inline-toggle" style={{ marginRight: 8 }}>
          <span>Enrôlement des postes</span>
          <Toggle checked={enrollment} onChange={handleToggleEnrollment} label="Enrôlement des postes" />
          <Badge tone={enrollment ? 'success' : 'neutral'} dot>{enrollment ? 'Actif' : 'Désactivé'}</Badge>
        </div>
        <Button icon="plus" onClick={onCreateBuilding}>Nouveau bâtiment</Button>
        <Button variant="primary" icon="plus" onClick={() => setShowRoomModal(true)}>Nouvelle salle</Button>
      </PageActions>

      <Toolbar search={search} onSearch={setSearch} placeholder="Rechercher un bâtiment…" />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: 16 }}>
        {visibleBuildings.map((building) => {
          const stats = buildingStats(building.id)
          const hasIssue = stats.issues > 0
          return (
            <div
              key={building.id}
              role="button"
              tabIndex={0}
              onClick={() => selectBuilding(building.id)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectBuilding(building.id) } }}
              style={{ cursor: 'pointer', textAlign: 'left' }}
            >
              <Card
                title={building.name}
                subtitle={building.description || building.id}
                actions={
                  hasIssue ? (
                    <Badge tone="warning">
                      <Icon name="alert" size={12} /> {stats.issues} souci{stats.issues > 1 ? 's' : ''}
                    </Badge>
                  ) : (
                    <Badge tone={stats.machinesCount > 0 ? 'success' : 'neutral'} dot>
                      {stats.machinesCount > 0 ? 'Opérationnel' : 'Aucun poste'}
                    </Badge>
                  )
                }
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginTop: 4 }}>
                  <div style={{ display: 'flex', gap: 14, fontSize: 13 }}>
                    <span><strong>{stats.roomsCount}</strong> salle{stats.roomsCount > 1 ? 's' : ''}</span>
                    <span><strong>{stats.machinesCount}</strong> PC</span>
                    {stats.offlineCount > 0 && (
                      <span style={{ color: 'var(--warning, #d97706)', fontWeight: 600 }}>
                        {stats.offlineCount} hors ligne
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }} onClick={(e) => e.stopPropagation()}>
                    <IconButton
                      icon="trash"
                      label={`Supprimer ${building.name}`}
                      onClick={async () => {
                        try {
                          await api.deleteBuilding(building.id)
                          notify(`Bâtiment ${building.name} supprimé.`, 'info')
                        } catch (err) {
                          notify(err.message || 'Impossible de supprimer ce bâtiment.', 'danger')
                        }
                      }}
                    />
                    <Button size="sm" variant="primary" icon="chevronRight" onClick={() => selectBuilding(building.id)}>
                      Ouvrir
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )
        })}
      </div>

      <RoomModal
        open={showRoomModal}
        name={newRoomName}
        onNameChange={setNewRoomName}
        buildingId={selectedBuilding}
        onBuildingChange={setSelectedBuilding}
        buildings={buildings}
        onClose={() => setShowRoomModal(false)}
        onCreate={createRoom}
      />
    </>
  )
}
