import React from 'react'
import { StatCard } from '../../../components.jsx'

// Les compteurs reprennent le code couleur documenté dans
// docs/admin-ui-couleurs-etats.md (vert = en ligne, ambre = MAJ en attente).
export default function BuildingSummary({ rooms, machines }) {
  const online = machines.filter((machine) => machine.status === 'online').length
  const updates = machines.filter((machine) => machine.updates > 0).length

  return (
    <div className="stat-grid four building-stats">
      <StatCard icon="building" label="Salles" value={rooms.length} tone="brand" hint="Salles inventoriées" />
      <StatCard icon="monitor" label="Postes" value={machines.length} tone="info" hint="Postes rattachés" />
      <StatCard icon="checkCircle" label="En ligne" value={online} tone="success" hint="Postes joignables" />
      <StatCard icon="download" label="MAJ en attente" value={updates} tone="warning" hint="Postes à traiter" />
    </div>
  )
}
