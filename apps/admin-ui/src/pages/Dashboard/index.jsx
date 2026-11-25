import React, { useEffect, useState } from 'react'
import { Button, PageActions } from '../../components.jsx'
import { api } from '../../api/client.js'
import ActivityCard from './components/ActivityCard.jsx'
import BuildingDistribution from './components/BuildingDistribution.jsx'
import ConnectedServices from './components/ConnectedServices.jsx'
import DashboardStats from './components/DashboardStats.jsx'
import QuickActions from './components/QuickActions.jsx'
import SystemCard from './components/SystemCard.jsx'
import './Dashboard.css'

export default function Dashboard({ notify, navigate, buildings }) {
  const [rooms, setRooms] = useState([])
  const [machines, setMachines] = useState([])
  const [services, setServices] = useState([])
  const [activity, setActivity] = useState([])
  const [serverInfo, setServerInfo] = useState({
    version: '—',
    build: '—',
    domain: 'lyux.lan',
    uptime: 'En ligne',
    cpu: '—',
    ram: '—',
    disk: '—',
  })

  const loadData = () => {
    api.getRooms()
      .then((list) => {
        if (Array.isArray(list)) {
          setRooms(list.map((r) => ({ ...r, buildingId: r.building_id || r.buildingId })))
        }
      })
      .catch(() => {})

    api.getInventory()
      .then((res) => {
        if (Array.isArray(res?.machines)) {
          setMachines(res.machines.map((m) => ({
            ...m,
            updates: m.is_up_to_date ? 0 : 1,
          })))
        }
      })
      .catch(() => {})

    api.health()
      .then((res) => {
        if (Array.isArray(res?.services)) setServices(res.services)
      })
      .catch(() => {})

    Promise.all([
      api.getSettings().catch(() => null),
      api.getSetup().catch(() => null),
      api.dashboardSummary().catch(() => null),
    ]).then(([sys, setup, summary]) => {
      setServerInfo((prev) => ({
        ...prev,
        version: sys?.lyux_version || summary?.server_version || prev.version,
        build: sys?.lyux_build || prev.build,
        domain: setup?.domain || prev.domain,
      }))
      if (Array.isArray(summary?.recent_tickets)) {
        setActivity(summary.recent_tickets.map((t) => ({
          id: t.id,
          time: t.time || '',
          title: t.title,
          detail: `${t.author} · ${t.status}`,
          tone: t.status === 'Résolu' ? 'success' : 'info',
          icon: 'info',
        })))
      }
    })
  }

  useEffect(() => {
    loadData()
  }, [])

  const online = machines.filter((machine) => machine.status === 'online').length
  const outdated = machines.filter((machine) => machine.updates > 0).length
  const activeServices = services.filter((item) => item.status === 'active').length

  const handleCheckUpdates = async () => {
    try {
      const res = await api.checkUpdates()
      notify(res.message || 'Vérification terminée.', 'info')
      loadData()
    } catch (err) {
      notify(err.message || 'Erreur lors de la vérification.', 'danger')
    }
  }

  return (
    <>
      <PageActions>
        <Button icon="refresh" onClick={handleCheckUpdates}>
          Vérifier les mises à jour
        </Button>
        <Button variant="primary" icon="users" onClick={() => navigate('utilisateurs')}>
          Gérer les comptes
        </Button>
      </PageActions>

      <DashboardStats
        online={online}
        machineCount={machines.length}
        roomCount={rooms.length}
        buildingCount={buildings.length}
        outdated={outdated}
      />

      <div className="grid-2-1">
        <ActivityCard items={activity} notify={notify} />
        <SystemCard serverInfo={serverInfo} />
      </div>

      <div className="grid-1-1">
        <BuildingDistribution buildings={buildings} machines={machines} rooms={rooms} />
        <ConnectedServices services={services} activeCount={activeServices} />
      </div>

      <QuickActions navigate={navigate} />
    </>
  )
}
