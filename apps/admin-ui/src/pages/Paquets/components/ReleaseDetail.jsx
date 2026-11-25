import React from 'react'
import { Badge, Button, Card, KeyValue } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

const FAMILY_LABELS = { client: 'Client LyuX', os: 'Système', logiciel: 'Logiciel' }
const STATE_LABELS = {
  published: 'Publiée',
  signed: 'Signée',
  draft: 'Brouillon',
  revoked: 'Révoquée',
  removed: 'Retirée',
  retired: 'Retirée',
}
const STATE_TONES = {
  published: 'success',
  signed: 'info',
  draft: 'warning',
  revoked: 'danger',
  removed: 'neutral',
  retired: 'neutral',
}

const shortHash = (value) => (value ? `${value.slice(0, 14)}…${value.slice(-6)}` : '—')

export default function ReleaseDetail({ release, onShowManifest, onSign, onPublish, onRevoke, onRollback }) {
  if (!release) return null

  const verified = release.signature === 'Vérifiée' && Boolean(release.detached_signature)
  const artifacts = Array.isArray(release.artifacts) ? release.artifacts : []

  return (
    <Card
      title="Détail de la version"
      subtitle={`${release.version} · build ${release.build}`}
      actions={<Badge tone={STATE_TONES[release.state] || 'neutral'} dot>{STATE_LABELS[release.state] || release.state}</Badge>}
      className="release-detail"
    >
      <div className="stacked">
        <KeyValue label="Famille" value={FAMILY_LABELS[release.family] || release.family || 'Client LyuX'} />
        <KeyValue label="Canal" value={release.channel === 'stable' ? 'Stable' : 'Test'} mono />
        <KeyValue label="Profil" value={release.profile_id || 'standard'} mono />
        <KeyValue label="Publication" value={release.published_at || release.publishedAt || 'Non publiée'} />
        <KeyValue label="Clé Ed25519" value={release.key_id || 'En attente'} mono />
        <KeyValue label="Empreinte du manifeste" value={<span title={release.manifest_hash || release.manifestHash}>{shortHash(release.manifest_hash || release.manifestHash)}</span>} mono />
      </div>

      <p className="release-notes">{release.notes}</p>

      <div className="release-detail-section">
        <h4>Artefacts du manifeste</h4>
        <div className="artifact-list">
          {artifacts.map((artifact) => (
            <div className="artifact-row" key={artifact.name}>
              <span className={`artifact-icon tone-${verified ? 'success' : 'warning'}`}>
                <Icon name={artifact.type === 'config' ? 'file' : 'package'} size={14} />
              </span>
              <span className="artifact-copy">
                <strong>{artifact.name}</strong>
                <small>{artifact.type} · {artifact.size} octets</small>
                <span className="artifact-hash mono" title={artifact.sha256}>SHA-256 {shortHash(artifact.sha256)}</span>
              </span>
              <Badge tone={verified ? 'success' : 'warning'} dot>{verified ? 'Signé' : 'À signer'}</Badge>
            </div>
          ))}
        </div>
      </div>

      <div className="detail-actions">
        <Button icon="shield" onClick={onShowManifest}>Voir le manifeste</Button>
        {(release.state === 'draft' || !verified) && (
          <Button icon="key" onClick={() => onSign && onSign(release)}>Signer (Ed25519)</Button>
        )}
        {(release.state === 'draft' || release.state === 'signed') && (
          <Button
            variant="primary"
            icon="check"
            disabled={!verified}
            onClick={() => onPublish && onPublish(release)}
          >
            Publier
          </Button>
        )}
        {release.state === 'published' && (
          <Button icon="alert" onClick={() => onRevoke && onRevoke(release)}>Révoquer</Button>
        )}
        {(release.state === 'signed' || release.state === 'retired') && (
          <Button icon="refresh" onClick={() => onRollback && onRollback(release)}>Restaurer</Button>
        )}
      </div>

      <div className="note-box release-note">
        <Icon name="lock" size={16} />
        <p>
          La publication exige une signature Ed25519 valide et une session administrateur authentifiée.
        </p>
      </div>
    </Card>
  )
}
