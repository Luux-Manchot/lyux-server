import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, PageActions } from '../../components.jsx'
import { api } from '../../api/client.js'
import RoomInfo from './components/RoomInfo.jsx'
import MachineCards from './components/MachineCards.jsx'
import './ParcSalle.css'

export default function ParcSalle({
  building,
  room,
  notify,
  navigate,
  navigateBuilding,
}) {
  const [machines, setMachines] = useState([])

  useEffect(() => {
    api.getMachines()
      .then((list) => {
        if (Array.isArray(list)) setMachines(list)
      })
      .catch(() => {})
  }, [room?.id])

  const roomMachines = useMemo(
    () => machines.filter((machine) => machine.room === room?.id),
    [machines, room?.id],
  )

  if (!building) {
    return (
      <Card title="Bâtiment introuvable">
        <p>Ce bâtiment n’existe pas dans le parc.</p>
        <Button variant="primary" icon="arrowLeft" onClick={() => navigate('parc')}>Retour à la liste des bâtiments</Button>
      </Card>
    )
  }

  if (!room) {
    return (
      <Card title="Salle introuvable">
        <p>Cette salle n’existe pas dans ce bâtiment.</p>
        <Button variant="primary" icon="arrowLeft" onClick={() => navigateBuilding(building)}>
          Retour à {building.name}
        </Button>
      </Card>
    )
  }

  const handleWakeRoom = async () => {
    try {
      await Promise.all(roomMachines.map((m) => api.wakeMachine(m.hostname, m.mac)))
      notify(`Paquets Wake-on-LAN envoyés aux ${roomMachines.length} postes de ${room.id}.`, 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors du réveil de la salle.', 'danger')
    }
  }

  const handleLockRoom = async () => {
    try {
      await api.lockRoom(room.id, 'lock', 'Attention au professeur')
      notify(`Salle ${room.id} verrouillée (Veyon).`, 'info')
    } catch (err) {
      notify(err.message || 'Erreur lors du verrouillage.', 'danger')
    }
  }

  return (
    <>
      <PageActions>
        <Button icon="arrowLeft" onClick={() => navigateBuilding(building)}>Retour au bâtiment</Button>
        <Button icon="lock" onClick={handleLockRoom}>Verrouiller la salle</Button>
        <Button variant="primary" icon="zap" onClick={handleWakeRoom}>
          Réveiller la salle
        </Button>
      </PageActions>

      <RoomInfo building={building} room={room} machines={roomMachines} />
      <MachineCards building={building} room={room} machines={roomMachines} />
    </>
  )
}
