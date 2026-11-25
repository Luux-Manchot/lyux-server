import React from 'react'
import { Badge, Button, Card, KeyValue, ProgressBar } from '../../../components.jsx'

export default function ClientFleetCard({ notify, autoUpdate, syncRate, upToDate, totalMachines = 0, targetVersion = '—', aptCache = true }) {
  return (
    <Card title="Parc client" subtitle="Distribution de la version cible">
      <div className="sync-overview">
        <div>
          <span className="sync-value">{syncRate} %</span>
          <span className="sync-label">postes synchronisés</span>
        </div>
        <ProgressBar value={syncRate} tone="success" />
      </div>
      <div className="stacked">
        <KeyValue label="Version cible" value={targetVersion} mono />
        <KeyValue label="Postes à jour" value={`${upToDate} / ${totalMachines}`} />
        <KeyValue label="Cache APT" value={<Badge tone={aptCache ? 'success' : 'neutral'} dot>{aptCache ? 'Actif · port 3142' : 'Désactivé'}</Badge>} />
        <KeyValue label="Mises à jour auto" value={<Badge tone={autoUpdate ? 'brand' : 'neutral'} dot>{autoUpdate ? 'Planifiées (nuit)' : 'Désactivées'}</Badge>} />
      </div>
      <Button variant="primary" icon="send" className="full-width" onClick={() => notify('Le déploiement automatique par lot arrivera avec le module Ansible/Agent.', 'info')}>
        Diffuser une mise à jour
      </Button>
    </Card>
  )
}
