import React from 'react'
import { Card, ProgressBar } from '../../../components.jsx'

export default function VersionDistribution({ machines = [], targetVersion = '1.0.0' }) {
  const counts = machines.reduce((acc, m) => {
    const v = m.version || 'Inconnue'
    acc[v] = (acc[v] || 0) + 1
    return acc
  }, {})

  const entries = Object.entries(counts)

  return (
    <Card title="Répartition des versions" subtitle="État des versions installées sur les postes">
      {entries.length === 0 ? (
        <p className="muted" style={{ margin: 0 }}>Aucune machine remontée par l’inventaire.</p>
      ) : (
        entries.map(([version, count]) => (
          <div className="building-bar" key={version}>
            <span className="bar-label">LyuX Client {version}</span>
            <ProgressBar
              value={machines.length ? Math.round((count / machines.length) * 100) : 0}
              tone={version === targetVersion ? 'success' : 'warning'}
            />
            <strong>{count} poste{count > 1 ? 's' : ''}</strong>
          </div>
        ))
      )}
    </Card>
  )
}
