import React, { useEffect, useState } from 'react'
import { Badge, Card, KeyValue } from '../../../components.jsx'
import { api } from '../../../api/client.js'

export default function SystemCard({ serverInfo }) {
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    api.systemMetrics()
      .then((res) => setMetrics(res))
      .catch(() => {})
  }, [])

  const cpuLabel = metrics
    ? `${metrics.cpu_cores} cœurs${metrics.load_1m != null ? ` · charge ${metrics.load_1m}` : ''}`
    : '—'
  const memLabel = metrics?.memory?.total_gb != null
    ? `${metrics.memory.used_gb} / ${metrics.memory.total_gb} Go (${metrics.memory.percent}%)`
    : 'Mesurée sur hôte Linux'
  const diskLabel = metrics?.disk?.total_gb != null
    ? `${metrics.disk.used_gb} / ${metrics.disk.total_gb} Go (${metrics.disk.percent}%)`
    : '—'

  return (
    <Card title="État du système" subtitle="Appliance LyuX Serveur (Admin UI :8087)">
      <div className="stacked">
        <KeyValue label="Version installée" value={serverInfo.version} mono />
        <KeyValue label="Domaine" value={serverInfo.domain || 'lyux.lan'} mono />
        <KeyValue label="Processeur" value={cpuLabel} mono />
        <KeyValue label="Mémoire RAM" value={memLabel} mono />
        <KeyValue label="Stockage" value={diskLabel} mono />
        <KeyValue label="Statut global">
          <Badge tone="success" dot>Opérationnel</Badge>
        </KeyValue>
      </div>
    </Card>
  )
}
