import React from 'react'
import { Badge, Button, KeyValue } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function MachineDetail({ machine, onWake, onMove, onRemove }) {
  return (
    <div className="pc-detail">
      <div className="subheading with-icon">
        <Icon name="monitor" size={16} />
        {machine ? machine.hostname : 'Détail du poste'}
      </div>
      {machine ? (
        <>
          <div className="stacked">
            <KeyValue label="Statut" value={<Badge tone={machine.status === 'online' ? 'success' : 'neutral'} dot>{machine.status === 'online' ? 'En ligne' : 'Hors ligne'}</Badge>} />
            <KeyValue label="Version LyuX" value={machine.version} mono />
            <KeyValue label="Build" value={machine.build} mono />
            <KeyValue label="Adresse IP" value={machine.ip} mono />
            <KeyValue label="Adresse MAC" value={machine.mac} mono />
            <KeyValue label="Session active" value={machine.session} />
            <KeyValue label="Mises à jour" value={machine.updates === 0 ? 'À jour' : `${machine.updates} en attente`} />
          </div>
          <div className="detail-actions">
            <Button icon="zap" onClick={onWake}>Réveiller (WOL)</Button>
            <Button icon="arrowUpRight" onClick={onMove}>Déplacer vers une salle</Button>
            <Button variant="danger" icon="trash" onClick={onRemove}>Retirer du parc</Button>
          </div>
        </>
      ) : (
        <div className="hint-box">
          <Icon name="info" size={18} />
          <p>Sélectionnez un poste pour afficher sa configuration et ses actions rapides.</p>
        </div>
      )}
    </div>
  )
}
