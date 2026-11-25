import React from 'react'
import { Badge, Button, Card, KeyValue } from '../../../components.jsx'
import { api } from '../../../api/client.js'

export default function ServerCard({ notify, serverSettings }) {
  const handleApply = async () => {
    try {
      const res = await api.applyUpdates()
      notify(res.message || 'Mise à jour appliquée.', 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors de la mise à jour serveur.', 'danger')
    }
  }

  return (
    <Card title="Infrastructure LyuX Serveur" subtitle="Version et état de l’appliance">
      <div className="stacked">
        <KeyValue label="Version installée" value={serverSettings?.lyux_version || '—'} mono />
        <KeyValue label="Build / révision" value={serverSettings?.lyux_build || '—'} mono />
        <KeyValue label="Dépôt source" value={serverSettings?.github_repo || '—'} mono />
        <KeyValue label="Branche" value={serverSettings?.github_branch || 'main'} mono />
        <KeyValue label="Statut système"><Badge tone="success" dot>Opérationnel</Badge></KeyValue>
      </div>
      <Button icon="download" className="full-width" onClick={handleApply}>
        Appliquer les mises à jour serveur
      </Button>
    </Card>
  )
}
