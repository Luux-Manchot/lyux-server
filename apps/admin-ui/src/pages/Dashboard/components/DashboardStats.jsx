import React from 'react'
import { StatCard } from '../../../components.jsx'

export default function DashboardStats({ online, machineCount, roomCount, buildingCount, outdated }) {
  return (
    <div className="stat-grid">
      <StatCard icon="monitor" label="Postes en ligne" value={`${online} / ${machineCount}`} hint="Sur l'ensemble du parc" tone="success" trend="+2 aujourd'hui" />
      <StatCard icon="building" label="Salles configurées" value={roomCount} hint={`${buildingCount} bâtiments`} tone="brand" />
      <StatCard icon="graduation" label="Élèves inscrits" value="106" hint="Année 2026 – 2027" tone="violet" />
      <StatCard icon="download" label="Mises à jour en attente" value={outdated} hint="Postes à mettre à niveau" tone="warning" />
    </div>
  )
}
