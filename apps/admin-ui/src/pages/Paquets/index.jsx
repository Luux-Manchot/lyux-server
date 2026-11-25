import React, { useCallback, useEffect, useState } from 'react'
import { Button, PageActions, Tabs } from '../../components.jsx'
import { api } from '../../api/client.js'
import RegistrySummary from './components/RegistrySummary.jsx'
import ReleaseList from './components/ReleaseList.jsx'
import ReleaseDetail from './components/ReleaseDetail.jsx'
import ManifestPanel from './components/ManifestPanel.jsx'
import PolicyPanel from './components/PolicyPanel.jsx'
import './Paquets.css'

const DEFAULT_POLICY = {
  auto_publish_security: true,
  require_ed25519: true,
  allow_rollback: true,
  retention_count: 5,
}
const registryStatus = { status: 'En ligne', signed: true }
const serverInfo = { version: '1.0.0', build: 'trixie-prod', repository: 'apt.lyux.lan' }

export default function Paquets({ notify }) {
  const [tab, setTab] = useState('registre')
  const [releases, setReleases] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [policy, setPolicy] = useState(DEFAULT_POLICY)
  const [publicKeys, setPublicKeys] = useState(null)
  const [apiError, setApiError] = useState('')

  const loadReleases = useCallback(async () => {
    try {
      const res = await api.getReleases()
      const list = Array.isArray(res?.releases) ? res.releases : []
      setReleases(list)
      setApiError('')
      if (list.length > 0) {
        setSelectedId((prev) => (list.some((r) => r.id === prev) ? prev : list[0].id))
      }
      if (res?.policy) {
        setPolicy((prev) => ({ ...prev, ...res.policy }))
      }
      if (res?.public_keys) {
        setPublicKeys(res.public_keys)
      }
    } catch (err) {
      setApiError(err?.message || 'Registre serveur inaccessible')
    }
  }, [])

  useEffect(() => {
    loadReleases()
  }, [loadReleases])

  const selected = releases.find((release) => release.id === selectedId) || releases[0] || null
  const published = releases.filter((release) => release.state === 'published')

  const handleAction = async (fn, successMsg) => {
    try {
      await fn()
      await loadReleases()
      notify(successMsg, 'success')
    } catch (err) {
      notify(err?.message || 'Erreur lors de l’opération serveur.', 'warning')
    }
  }

  const updatePolicy = async (key, value, label) => {
    const next = { ...policy, [key]: value }
    setPolicy(next)
    try {
      await api.updateReleasePolicy({ [key]: value })
      if (label) notify(`${label} enregistré.`, 'info')
    } catch (err) {
      if (label) notify(err?.message || 'Erreur de sauvegarde politique.', 'warning')
    }
  }

  return (
    <>
      <PageActions>
        <Button
          icon="refresh"
          onClick={async () => {
            await loadReleases()
            notify(`Registre actualisé : ${published.length} version(s) publiée(s).`, 'info')
          }}
        >
          Vérifier le registre
        </Button>
        <Button
          variant="primary"
          icon="plus"
          onClick={() => {
            const ver = window.prompt('Version du brouillon (ex: 1.0.1) :', '1.0.1')
            if (!ver) return
            handleAction(
              () => api.createRelease({ version: ver.trim(), profile_id: 'standard', channel: 'stable' }),
              `Brouillon ${ver.trim()} créé dans le registre.`
            )
          }}
        >
          Déposer une version
        </Button>
      </PageActions>

      {apiError && (
        <div className="note-box" style={{ marginBottom: 12 }}>
          <p>Registre hors ligne : {apiError}</p>
        </div>
      )}

      <RegistrySummary
        serverVersion={serverInfo.version}
        publishedCount={published.length}
        signedCount={releases.filter((release) => release.signature === 'Vérifiée').length}
        draftCount={releases.filter((release) => release.state === 'draft').length}
      />

      <Tabs
        tabs={[
          { id: 'registre', label: 'Registre des versions', icon: 'boxes', count: releases.length },
          { id: 'manifeste', label: 'Manifeste signé', icon: 'shield' },
          { id: 'politique', label: 'Politique de mise à jour', icon: 'settings' },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === 'registre' && (
        <div className="paquets-split">
          <ReleaseList releases={releases} selectedId={selected?.id} onSelect={setSelectedId} />
          <ReleaseDetail
            release={selected}
            onShowManifest={() => setTab('manifeste')}
            onSign={(rel) => handleAction(() => api.signRelease(rel.id), `Release ${rel.version} signée Ed25519.`)}
            onPublish={(rel) => handleAction(() => api.publishRelease(rel.id), `Release ${rel.version} publiée.`)}
            onRevoke={(rel) => handleAction(() => api.revokeRelease(rel.id, 'Révocation administrateur'), `Release ${rel.version} révoquée.`)}
            onRollback={(rel) => handleAction(() => api.rollbackRelease(rel.id), `Restauration vers ${rel.version} effectuée.`)}
          />
        </div>
      )}

      {tab === 'manifeste' && <ManifestPanel release={selected} registry={registryStatus} publicKeys={publicKeys} notify={notify} />}

      {tab === 'politique' && (
        <PolicyPanel policy={policy} onChange={updatePolicy} registry={registryStatus} />
      )}
    </>
  )
}
