import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, PageActions } from '../../components.jsx'
import { api } from '../../api/client.js'
import BuildingSummary from './components/BuildingSummary.jsx'
import RoomList from './components/RoomList.jsx'
import './ParcBatiment.css'

export default function ParcBatiment({ building, navigate, onCreateBuilding, onOpenRoom }) {
  const [rooms, setRooms] = useState([])
  const [machines, setMachines] = useState([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (!building?.id) return
    api.getRooms(building.id)
      .then((list) => {
        if (Array.isArray(list)) {
          setRooms(list.map((r) => ({ ...r, buildingId: r.building_id || r.buildingId })))
        }
      })
      .catch(() => {})
    api.getMachines()
      .then((list) => {
        if (Array.isArray(list)) setMachines(list)
      })
      .catch(() => {})
  }, [building?.id])

  const buildingRooms = useMemo(
    () => rooms.filter((room) => room.buildingId === building?.id),
    [rooms, building?.id],
  )
  const buildingMachines = useMemo(
    () => machines.filter((machine) => buildingRooms.some((room) => room.id === machine.room)),
    [machines, buildingRooms],
  )

  if (!building) {
    return (
      <Card title="Bâtiment introuvable">
        <p>Ce bâtiment n’existe pas ou a été supprimé.</p>
        <Button variant="primary" icon="arrowLeft" onClick={() => navigate('parc')}>Retour à la liste des bâtiments</Button>
      </Card>
    )
  }

  return (
    <>
      <PageActions>
        <Button icon="arrowLeft" onClick={() => navigate('parc')}>Tous les bâtiments</Button>
        <Button variant="primary" icon="plus" onClick={onCreateBuilding}>Nouveau bâtiment</Button>
      </PageActions>

      <BuildingSummary rooms={buildingRooms} machines={buildingMachines} />

      <RoomList
        building={building}
        rooms={buildingRooms}
        machines={buildingMachines}
        search={search}
        onSearch={setSearch}
        onOpenRoom={onOpenRoom}
      />
    </>
  )
}
