import React, { useEffect, useState } from 'react'
import { Badge, Card } from '../../../components.jsx'
import { api } from '../../../api/client.js'

export default function ServerBuildCard() {
  const [info, setInfo] = useState({ version: '1.0.0', build: 'trixie-prod', repository: 'apt.lyux.lan' })

  useEffect(() => {
    api.dashboardSummary()
      .then((res) => {
        if (res?.server_version) {
          setInfo((prev) => ({ ...prev, version: res.server_version }))
        }
      })
      .catch(() => {})
  }, [])

  return (
    <Card title="Version du serveur" subtitle="Informations de build">
      <div className="stacked">
        <div className="key-value"><span className="key-label">Version</span><span className="mono">{info.version}</span></div>
        <div className="key-value"><span className="key-label">Build</span><span className="mono">{info.build}</span></div>
        <div className="key-value"><span className="key-label">Dépôt</span><span className="mono">{info.repository}</span></div>
        <div className="key-value"><span className="key-label">Statut</span><Badge tone="success" dot>À jour</Badge></div>
      </div>
    </Card>
  )
}
