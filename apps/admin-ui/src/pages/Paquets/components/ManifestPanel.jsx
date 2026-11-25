import React from 'react'
import { Badge, Button, Card, DataTable, KeyValue } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function ManifestPanel({ release, registry, publicKeys, notify }) {
  if (!release) return null

  const verified = release.signature === 'Vérifiée' && Boolean(release.detached_signature)
  const artifacts = Array.isArray(release.artifacts) ? release.artifacts : []

  return (
    <Card
      title="Manifeste signé Ed25519"
      subtitle={`Intégrité des artefacts de ${release.version}`}
      actions={
        <Button
          size="sm"
          icon="shield"
          onClick={() => notify && notify(
            verified
              ? `Empreintes SHA-256 et signature Ed25519 vérifiées (${release.key_id || 'clé active'}).`
              : `Manifeste en attente de signature Ed25519 pour ${release.version}.`,
            verified ? 'success' : 'warning'
          )}
        >
          Vérifier les empreintes
        </Button>
      }
    >
      <div className="manifest-summary">
        <div className="stacked">
          <KeyValue label="Version" value={`${release.version} · build ${release.build}`} mono />
          <KeyValue label="Algorithme d’empreinte" value="SHA-256" mono />
          <KeyValue label="Signature détachée" value={release.detached_signature ? `${release.detached_signature.slice(0, 22)}…` : 'Absente'} mono />
          <KeyValue label="Clé publique active" value={publicKeys?.active_key_id || release.key_id || '—'} mono />
          <KeyValue label="Stockage des artefacts" value={registry.storage} mono />
          <KeyValue label="Accès API" value="/api/v1/client/profile-manifest" mono />
        </div>
        <div className="manifest-status">
          <span className={`manifest-status-icon tone-${verified ? 'success' : 'warning'}`}>
            <Icon name={verified ? 'checkCircle' : 'alert'} size={26} />
          </span>
          <strong>{verified ? 'Manifeste signé' : 'Signature en attente'}</strong>
          <p>{verified
            ? 'Le client vérifie la signature Ed25519 et chaque SHA-256 avant application.'
            : 'Cette version ne peut pas être publiée tant que le manifeste n’est pas signé.'}</p>
          <Badge tone={verified ? 'success' : 'warning'} dot>{release.signature}</Badge>
        </div>
      </div>

      <DataTable
        columns={[
          { key: 'name', label: 'Artefact', render: (artifact) => <strong className="mono">{artifact.name}</strong> },
          { key: 'type', label: 'Format', render: (artifact) => <Badge tone="neutral">{artifact.type}</Badge> },
          { key: 'size', label: 'Taille', render: (artifact) => <span className="muted">{artifact.size} octets</span> },
          { key: 'sha256', label: 'Empreinte SHA-256', render: (artifact) => <span className="mono artifact-hash" title={artifact.sha256}>{artifact.sha256}</span> },
          {
            key: 'check',
            label: 'Vérification',
            render: () => <Badge tone={verified ? 'success' : 'warning'} dot>{verified ? 'Signé' : 'En attente'}</Badge>,
          },
        ]}
        rows={artifacts}
        footer={false}
        emptyLabel="Aucun artefact dans ce manifeste."
      />

      <div className="note-box">
        <Icon name="info" size={16} />
        <p>
          Le client refuse tout artefact dont l’empreinte SHA-256 ou la signature Ed25519 ne correspond pas
          au manifeste diffusé par le serveur.
        </p>
      </div>
    </Card>
  )
}
