import React from 'react'
import { Card, Select, SettingRow, Toggle } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function PolicyPanel({ policy, onChange, registry }) {
  return (
    <Card
      title="Politique de mise à jour"
      subtitle="Détection, distribution et application restent distinctes"
      className="policy-panel"
    >
      <SettingRow
        icon="zap"
        title="Application automatique"
        description="Appliquer la version cible dès qu’elle est publiée sur le canal suivi."
        control={
          <Toggle
            checked={policy.autoApply}
            label="Application automatique"
            onChange={(value) => onChange('autoApply', value, `Application automatique ${value ? 'activée' : 'désactivée'}`)}
          />
        }
      />
      <SettingRow
        icon="layers"
        title="Canal suivi"
        description="Les versions du canal Test ne sont pas diffusées au parc sans changement explicite."
        control={
          <Select
            label="Canal suivi"
            value={policy.channel}
            onChange={(value) => onChange('channel', value, `Canal suivi : ${value === 'stable' ? 'Stable' : 'Test'}`)}
            options={[{ value: 'stable', label: 'Stable' }, { value: 'test', label: 'Test' }]}
          />
        }
      />
      <SettingRow
        icon="clock"
        title="Fenêtre de maintenance"
        description="Aucune application automatique n’est déclenchée pendant les heures de cours."
        control={
          <Select
            label="Fenêtre de maintenance"
            value={policy.window}
            onChange={(value) => onChange('window', value, `Fenêtre de maintenance : ${value}`)}
            options={[
              { value: '22:00 – 05:00', label: '22:00 – 05:00' },
              { value: '23:00 – 04:00', label: '23:00 – 04:00' },
              { value: 'Désactivée', label: 'Désactivée' },
            ]}
          />
        }
      />
      <SettingRow
        icon="shield"
        title="Validation administrative"
        description="Une personne autorisée doit confirmer chaque diffusion, même en dehors des cours."
        control={
          <Toggle
            checked={policy.requireApproval}
            label="Validation administrative"
            onChange={(value) => onChange('requireApproval', value, `Validation administrative ${value ? 'requise' : 'désactivée'}`)}
          />
        }
      />
      <SettingRow
        icon="refresh"
        title="Retour arrière"
        description="Conserver la version précédente et permettre un retour en cas d’incident."
        control={
          <Toggle
            checked={policy.rollback}
            label="Retour arrière"
            onChange={(value) => onChange('rollback', value, `Retour arrière ${value ? 'autorisé' : 'désactivé'}`)}
          />
        }
      />
      <SettingRow
        icon="lock"
        title="Artefacts signés uniquement"
        description="Obligation non négociable : aucun artefact non vérifié ne peut être distribué."
        control={
          <Toggle
            checked={policy.signedOnly}
            label="Artefacts signés uniquement"
            disabled
            onChange={() => {}}
          />
        }
      />
      <SettingRow
        icon="building"
        title="Périmètre d’application"
        description="Le pilotage se fait par salle pour éviter de saturer le réseau du lycée."
        control={
          <Select
            label="Périmètre d’application"
            value={policy.scope}
            onChange={(value) => onChange('scope', value, `Périmètre : ${value === 'room' ? 'par salle' : 'tout le parc'}`)}
            options={[{ value: 'room', label: 'Par salle' }, { value: 'fleet', label: 'Tout le parc' }]}
          />
        }
      />

      <div className="note-box policy-note">
        <Icon name="info" size={16} />
        <p>
          Ces réglages alimenteront la route <span className="mono">PUT /api/v1/updates/policy</span>.
          Écritures protégées : {registry.auth}. Toute modification est signée et journalisée côté serveur.
        </p>
      </div>
    </Card>
  )
}
