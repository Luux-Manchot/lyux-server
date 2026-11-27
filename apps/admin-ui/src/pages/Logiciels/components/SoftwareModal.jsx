import React, { useEffect, useState } from 'react'
import { Badge, Button, FormField, Modal, Select } from '../../../components.jsx'
import { api } from '../../../api/client.js'

const SOURCES = [
  { value: 'Flathub', label: 'Flathub (Flatpak)' },
  { value: 'Dépôt Debian', label: 'Dépôt Debian (.deb)' },
  { value: 'Site officiel', label: 'Site officiel / autre' },
]

const AVAILABLE_ROLES = [
  { id: 'eleve', label: 'Élèves' },
  { id: 'prof', label: 'Enseignants' },
  { id: 'viesco', label: 'Vie scolaire' },
  { id: 'administration', label: 'Administration' },
  { id: 'admin', label: 'Admins' },
]

export default function SoftwareModal({ open, onClose, notify, onAdd, categories = [] }) {
  const [tab, setTab] = useState('store')
  const [storeQuery, setStoreQuery] = useState('')
  const [storeSource, setStoreSource] = useState('all')
  const [storeItems, setStoreItems] = useState([])
  const [loadingStore, setLoadingStore] = useState(false)
  const [selectedStoreApp, setSelectedStoreApp] = useState(null)
  const [allowedRoles, setAllowedRoles] = useState(['eleve', 'prof', 'admin'])

  const initialForm = {
    name: '',
    package: '',
    link: '',
    source: 'Dépôt Debian',
    version: 'latest',
    category: categories[0] || 'Bureautique',
    target: 'Tous les postes',
    launchArgs: '',
  }
  const [form, setForm] = useState(initialForm)

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }))
  const toggleRole = (roleId) => {
    setAllowedRoles((current) =>
      current.includes(roleId) ? current.filter((r) => r !== roleId) : [...current, roleId],
    )
  }

  const runSearch = async (q = storeQuery, src = storeSource) => {
    setLoadingStore(true)
    try {
      const res = await api.searchAppStore(q, src)
      setStoreItems(Array.isArray(res?.items) ? res.items : [])
    } catch {
      setStoreItems([])
    } finally {
      setLoadingStore(false)
    }
  }

  useEffect(() => {
    if (open) {
      runSearch('', 'all')
    }
  }, [open])

  const close = () => {
    setForm({ ...initialForm })
    setSelectedStoreApp(null)
    setAllowedRoles(['eleve', 'prof', 'admin'])
    onClose()
  }

  const submit = () => {
    const roles = allowedRoles.length ? allowedRoles : ['eleve', 'prof', 'admin']
    if (tab === 'store') {
      if (!selectedStoreApp) {
        notify('Sélectionnez d’abord une application dans le Store.', 'warning')
        return
      }
      onAdd({
        name: selectedStoreApp.name,
        package: selectedStoreApp.package,
        category: selectedStoreApp.category || 'Général',
        source: selectedStoreApp.source || 'Flathub',
        format: selectedStoreApp.format || 'Flatpak',
        version: selectedStoreApp.version || 'latest',
        description: selectedStoreApp.description || '',
        icon: selectedStoreApp.icon || '📦',
        link: selectedStoreApp.link || '',
        target: 'Tous les postes',
        allowedRoles: roles,
        launchArgs: '',
      })
      close()
      return
    }

    if (!form.name.trim()) {
      notify('Le nom de l’application est obligatoire.', 'warning')
      return
    }
    onAdd({
      ...form,
      name: form.name.trim(),
      package: form.package.trim(),
      format: form.source === 'Flathub' ? 'Flatpak' : 'Paquet .deb',
      link: form.link.trim(),
      target: form.target.trim() || 'Tous les postes',
      allowedRoles: roles,
      version: form.version.trim() || 'latest',
      launchArgs: form.launchArgs.trim(),
    })
    close()
  }

  return (
    <Modal
      open={open}
      title="Store d’applications LyuX (Discover)"
      subtitle="Recherchez sur Flathub & Debian APT, choisissez les rôles autorisés et déployez automatiquement sur les postes."
      onClose={close}
      width="860px"
      footer={
        <>
          <Button onClick={close}>Annuler</Button>
          <Button variant="primary" icon="download" onClick={submit}>
            Ajouter & Installer sur le parc
          </Button>
        </>
      }
    >
      <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
        <Button size="sm" variant={tab === 'store' ? 'primary' : 'default'} onClick={() => setTab('store')}>
          Explorer le Store (Flathub & APT)
        </Button>
        <Button size="sm" variant={tab === 'manual' ? 'primary' : 'default'} onClick={() => setTab('manual')}>
          Ajout manuel (.deb / Flatpak)
        </Button>
      </div>

      {tab === 'store' ? (
        <div className="form-stack">
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              style={{ flex: 1 }}
              value={storeQuery}
              onChange={(e) => setStoreQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && runSearch(storeQuery, storeSource)}
              placeholder="Rechercher une application (ex. Inkscape, VLC, Blender, VS Code, Krita…)"
            />
            <Select
              value={storeSource}
              onChange={(val) => {
                setStoreSource(val)
                runSearch(storeQuery, val)
              }}
              options={[
                { value: 'all', label: 'Flathub + APT' },
                { value: 'flathub', label: 'Flathub' },
                { value: 'apt', label: 'Debian APT' },
              ]}
            />
            <Button icon="search" onClick={() => runSearch(storeQuery, storeSource)}>
              {loadingStore ? 'Recherche…' : 'Rechercher'}
            </Button>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
              gap: '10px',
              maxHeight: '280px',
              overflowY: 'auto',
              padding: '4px',
            }}
          >
            {storeItems.map((item) => {
              const isSel = selectedStoreApp?.id === item.id
              return (
                <button
                  key={`${item.source}-${item.id}`}
                  type="button"
                  onClick={() => setSelectedStoreApp(item)}
                  style={{
                    textAlign: 'left',
                    padding: '10px',
                    borderRadius: '8px',
                    border: isSel ? '2px solid var(--accent, #2563eb)' : '1px solid var(--border, #d1d5db)',
                    background: isSel ? 'rgba(37, 99, 235, 0.08)' : 'var(--surface, #fff)',
                    cursor: 'pointer',
                    display: 'flex',
                    gap: '10px',
                    alignItems: 'flex-start',
                  }}
                >
                  {item.icon ? (
                    <img src={item.icon} alt="" style={{ width: '32px', height: '32px', borderRadius: '6px', objectFit: 'contain' }} />
                  ) : (
                    <span style={{ fontSize: '22px', lineHeight: '32px' }}>📦</span>
                  )}
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '6px', alignItems: 'center' }}>
                      <strong style={{ fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.name}
                      </strong>
                      <Badge tone={item.format === 'Flatpak' ? 'info' : 'neutral'}>{item.format}</Badge>
                    </div>
                    <small style={{ display: 'block', color: '#6b7280', marginTop: '2px', fontSize: '11px' }}>
                      {item.package}
                    </small>
                    <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#4b5563', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {item.description || 'Application disponible sur le dépôt.'}
                    </p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ) : (
        <div className="form-stack">
          <FormField label="Nom de l’application">
            <input value={form.name} onChange={(event) => update('name', event.target.value)} placeholder="Ex. Inkscape" />
          </FormField>
          <FormField label="Identifiant paquet (.deb ou Flatpak ID)" hint="Ex. inkscape ou org.inkscape.Inkscape">
            <input value={form.package} onChange={(event) => update('package', event.target.value)} placeholder="Ex. inkscape" />
          </FormField>
          <FormField label="Source">
            <Select value={form.source} onChange={(value) => update('source', value)} options={SOURCES} />
          </FormField>
          <FormField label="Catégorie">
            <Select
              value={form.category}
              onChange={(value) => update('category', value)}
              options={categories.map((item) => ({ value: item, label: item }))}
            />
          </FormField>
          <FormField label="Lien du logiciel">
            <input type="url" value={form.link} onChange={(event) => update('link', event.target.value)} placeholder="https://exemple.fr/logiciel" />
          </FormField>
        </div>
      )}

      <div style={{ marginTop: '14px' }}>
        <FormField label="Rôles autorisés à exécuter cette application">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', paddingTop: '4px' }}>
            {AVAILABLE_ROLES.map((r) => (
              <label key={r.id} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={allowedRoles.includes(r.id)}
                  onChange={() => toggleRole(r.id)}
                />
                <span>{r.label}</span>
              </label>
            ))}
          </div>
        </FormField>
      </div>

      <p className="modal-note" style={{ marginTop: '10px' }}>
        <strong>Distribution optimisée :</strong> les clients téléchargent d’abord depuis le cache LAN du serveur
        (<code>apt-cacher-ng:3142</code>) ou le pair LAN le plus rapide, et basculent automatiquement sur Internet en cas
        d’indisponibilité. Seuls les rôles cochés peuvent voir et lancer l’application.
      </p>
    </Modal>
  )
}
