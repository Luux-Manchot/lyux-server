import React, { useMemo, useState } from 'react'
import { Badge, Card, DataTable, Select, Toolbar } from '../../../components.jsx'

const FAMILY_LABELS = { client: 'Client LyuX', os: 'Système', logiciel: 'Logiciel' }
const CHANNEL_LABELS = { stable: 'Stable', test: 'Test' }
const STATE_LABELS = { published: 'Publiée', draft: 'Brouillon', retired: 'Retirée' }
const STATE_TONES = { published: 'success', draft: 'warning', retired: 'neutral' }

export default function ReleaseList({ releases, selectedId, onSelect }) {
  const [search, setSearch] = useState('')
  const [family, setFamily] = useState('all')

  const rows = useMemo(() => {
    const term = search.trim().toLowerCase()
    return releases
      .filter((release) => family === 'all' || release.family === family)
      .filter((release) => !term
        || release.version.toLowerCase().includes(term)
        || release.build.includes(term)
        || FAMILY_LABELS[release.family].toLowerCase().includes(term)
        || release.target.toLowerCase().includes(term))
      .map((release) => ({
        ...release,
        _className: release.id === selectedId ? 'row-selected' : '',
      }))
  }, [releases, family, search, selectedId])

  return (
    <Card
      title="Registre des versions"
      subtitle="Sélectionnez une version pour afficher son manifeste"
    >
      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Rechercher une version, un build ou une cible…"
        filters={
          <Select
            label="Famille"
            value={family}
            onChange={setFamily}
            options={[
              { value: 'all', label: 'Toutes les familles' },
              { value: 'client', label: 'Client LyuX' },
              { value: 'os', label: 'Système' },
              { value: 'logiciel', label: 'Logiciel' },
            ]}
          />
        }
      />
      <DataTable
        columns={[
          {
            key: 'version',
            label: 'Version',
            render: (release) => (
              <span className="release-version">
                <strong>{release.version}</strong>
                <small>build {release.build}</small>
              </span>
            ),
          },
          { key: 'family', label: 'Famille', render: (release) => FAMILY_LABELS[release.family] },
          {
            key: 'channel',
            label: 'Canal',
            render: (release) => (
              <Badge tone={release.channel === 'stable' ? 'brand' : 'info'}>
                {CHANNEL_LABELS[release.channel]}
              </Badge>
            ),
          },
          {
            key: 'state',
            label: 'État',
            render: (release) => <Badge tone={STATE_TONES[release.state]} dot>{STATE_LABELS[release.state]}</Badge>,
          },
          { key: 'publishedAt', label: 'Publication', render: (release) => <span className="muted">{release.publishedAt}</span> },
        ]}
        rows={rows}
        onRowClick={(release) => onSelect(release.id)}
        emptyLabel="Aucune version ne correspond à ce filtre."
      />
    </Card>
  )
}
