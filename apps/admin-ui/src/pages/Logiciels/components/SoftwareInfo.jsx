import React from 'react'
import { Badge, Button, KeyValue } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'
import { api } from '../../../api/client.js'

const STATUS = {
  deployed: { label: 'Déployé', tone: 'success' },
  pending: { label: 'En attente', tone: 'warning' },
  draft: { label: 'Brouillon', tone: 'neutral' },
}

export default function SoftwareInfo({ app, notify }) {
  if (!app) {
    return (
      <div className="software-info-panel is-empty">
        <span className="software-info-empty-icon"><Icon name="package" size={22} /></span>
        <strong>Aucune application sélectionnée</strong>
        <p>Choisissez une application dans la liste pour afficher sa fiche.</p>
      </div>
    )
  }

  const status = STATUS[app.status] || STATUS.draft

  const handleDeploy = async () => {
    try {
      const res = await api.deployApps()
      notify(res?.message || `Déploiement de ${app.name} déclenché.`, 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors du déploiement.', 'danger')
    }
  }

  return (
    <div className="software-info-panel">
      <div className="software-info-head">
        <span className={`software-info-icon tone-${status.tone}`}><Icon name="package" size={17} /></span>
        <div className="software-info-title">
          <strong>{app.name}</strong>
          <small>{app.id} · version {app.version || '—'}</small>
        </div>
        <Badge tone={status.tone} dot>{status.label}</Badge>
      </div>

      {app.description && <p className="software-info-description">{app.description}</p>}

      <h4 className="software-info-heading">Fiche technique & déploiement</h4>
      <div className="stacked">
        <KeyValue label="Catégorie" value={app.category || '—'} />
        <KeyValue label="Version" value={app.version || '—'} mono />
        <KeyValue label="Format" value={app.format || 'Paquet .deb'} />
        <KeyValue label="Source" value={app.source || 'Dépôt LyuX'} />
        <KeyValue label="Public cible" value={app.target || 'Tous les postes'} />
        {app.link && <KeyValue label="Lien du projet" value={<span className="mono software-link" title={app.link}>{app.link}</span>} />}
        {app.license && <KeyValue label="Licence" value={app.license} mono />}
        <KeyValue
          label="Arguments de lancement"
          value={app.launchArgs || app.launch_args
            ? <span className="mono software-args" title={app.launchArgs || app.launch_args}>{app.launchArgs || app.launch_args}</span>
            : <span className="muted">Aucun argument</span>}
        />
      </div>

      {app.notes && (
        <div className="software-info-note">
          <Icon name="info" size={13} />
          <span>{app.notes}</span>
        </div>
      )}

      <div className="software-info-actions">
        <Button size="sm" variant="primary" icon="download" onClick={handleDeploy}>
          Déployer
        </Button>
      </div>
    </div>
  )
}
