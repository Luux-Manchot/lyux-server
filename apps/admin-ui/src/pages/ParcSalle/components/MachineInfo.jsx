import React from 'react'
import { Badge, KeyValue } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

// Panneau de droite : toutes les informations utiles sur le poste sélectionné.
export default function MachineInfo({ machine, building }) {
  if (!machine) {
    return (
      <aside className="machine-info-panel is-empty">
        <span className="machine-info-empty-icon"><Icon name="monitor" size={22} /></span>
        <strong>Aucun poste sélectionné</strong>
        <p>Cliquez sur un poste de la liste pour afficher ses informations détaillées.</p>
      </aside>
    )
  }

  const online = machine.status === 'online'
  const session = machine.session && machine.session !== 'Aucune' ? machine.session : 'Aucune session'
  const sessionLabel = machine.session === 'Session libre' ? 'Poste libre' : session

  return (
    <aside className="machine-info-panel" aria-live="polite">
      <div className="machine-info-head">
        <span className={`machine-icon ${machine.status}`}><Icon name="monitor" size={17} /></span>
        <div className="machine-info-title">
          <strong>{machine.hostname}</strong>
          <small>{machine.id} · salle {machine.room}</small>
        </div>
        <Badge tone={online ? 'success' : 'neutral'} dot>
          {online ? 'En ligne' : 'Hors ligne'}
        </Badge>
      </div>

      <div className={`machine-info-lastseen ${online ? 'online' : 'offline'}`}>
        <Icon name="clock" size={14} />
        <div>
          <small>Dernière connexion</small>
          <strong>{machine.lastSeen || 'Non renseignée'}</strong>
        </div>
      </div>

      <div className="machine-info-section">
        <h4>Session et disponibilité</h4>
        <KeyValue label="Utilisateur / session" value={sessionLabel} />
        <KeyValue label="Disponibilité" value={machine.uptime || '—'} mono />
        <KeyValue
          label="Mises à jour"
          value={machine.updates > 0
            ? <Badge tone="warning"><Icon name="download" size={11} /> {machine.updates} paquets en attente</Badge>
            : <Badge tone="success" dot>À jour</Badge>}
        />
      </div>

      <div className="machine-info-section">
        <h4>Réseau</h4>
        <KeyValue label="Adresse IP" value={machine.ip} mono />
        <KeyValue label="Adresse MAC" value={machine.mac} mono />
      </div>

      <div className="machine-info-section">
        <h4>Système</h4>
        <KeyValue label="Client LyuX" value={machine.version} mono />
        <KeyValue label="Build" value={machine.build} mono />
        <KeyValue label="Salle" value={machine.room} />
        <KeyValue label="Bâtiment" value={building?.name || '—'} />
      </div>

      <p className="machine-info-note">Synchronisé avec l’API LyuX</p>
    </aside>
  )
}
