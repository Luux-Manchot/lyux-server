import React from 'react'
import { Badge, Button, KeyValue } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'
import { api } from '../../../api/client.js'

const STATUS = {
  deployed: { label: 'Déployé', tone: 'success' },
  pending: { label: 'En attente', tone: 'warning' },
  draft: { label: 'Brouillon', tone: 'neutral' },
}

const AVAILABLE_ROLES = [
  { id: 'eleve', label: 'Élèves' },
  { id: 'prof', label: 'Enseignants' },
  { id: 'viesco', label: 'Vie scolaire' },
  { id: 'administration', label: 'Administration' },
  { id: 'admin', label: 'Admins' },
]

export default function SoftwareInfo({ app, notify, onUpdated, onDeleted }) {
  if (!app) {
    const currentRoles = app.allowed_roles || app.allowed_groups || ['eleve', 'prof', 'admin']

  const toggleRole = async (roleId) => {
    const next = currentRoles.includes(roleId)
      ? currentRoles.filter((r) => r !== roleId)
      : [...currentRoles, roleId]
    try {
      const res = await api.updateApp(app.id, { allowed_roles: next })
      if (onUpdated && res?.app) onUpdated(res.app)
      notify(`Droits mis à jour pour ${app.name}.`, 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors de la mise à jour des droits.', 'danger')
    }
  }

  const handleDelete = async () => {
    try {
      await api.deleteApp(app.id)
      if (onDeleted) onDeleted(app.id)
      notify(`${app.name} retiré du catalogue.`, 'info')
    } catch (err) {
      notify(err.message || 'Erreur lors de la suppression.', 'danger')
    }
  }

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

  const currentRoles = app.allowed_roles || app.allowed_groups || ['eleve', 'prof', 'admin']

  const toggleRole = async (roleId) => {
    const next = currentRoles.includes(roleId)
      ? currentRoles.filter((r) => r !== roleId)
      : [...currentRoles, roleId]
    try {
      const res = await api.updateApp(app.id, { allowed_roles: next })
      if (onUpdated && res?.app) onUpdated(res.app)
      notify(`Droits mis à jour pour ${app.name}.`, 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors de la mise à jour des droits.', 'danger')
    }
  }

  const handleDelete = async () => {
    try {
      await api.deleteApp(app.id)
      if (onDeleted) onDeleted(app.id)
      notify(`${app.name} retiré du catalogue.`, 'info')
    } catch (err) {
      notify(err.message || 'Erreur lors de la suppression.', 'danger')
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
        <KeyValue label="Paquet / ID" value={app.package || app.id} mono />
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

      <h4 className="software-info-heading" style={{ marginTop: '14px' }}>Rôles autorisés à exécuter</h4>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
        {AVAILABLE_ROLES.map((r) => (
          <label key={r.id} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px' }}>
            <input
              type="checkbox"
              checked={currentRoles.includes(r.id) || currentRoles.includes(r.id === 'eleve' ? 'eleves' : r.id === 'prof' ? 'enseignants' : r.id)}
              onChange={() => toggleRole(r.id)}
            />
            <span>{r.label}</span>
          </label>
        ))}
      </div>

      <div className="software-info-actions" style={{ display: 'flex', gap: '8px' }}>
        <Button size="sm" variant="primary" icon="download" onClick={handleDeploy}>
          Déployer
        </Button>
        <Button size="sm" icon="trash" onClick={handleDelete}>
          Retirer
        </Button>
      </div>
    </div>
  )
}
