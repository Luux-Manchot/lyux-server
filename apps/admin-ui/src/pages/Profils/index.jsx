import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Badge, Button, Card, FormField, IconButton, Modal, PageActions, Select, Toggle } from '../../components.jsx'
import { api } from '../../api/client.js'

const SCOPE_LABELS = {
  global: 'Tout le lycée',
  role: 'Rôle',
  group: 'Classe / Groupe',
  user: 'Utilisateur',
  machine: 'Poste spécifique',
}

const THEME_SWATCHES = {
  'lyux-ocean': '#0284c7',
  'lyux-dark': '#1e293b',
  'lyux-light': '#e2e8f0',
}

const SYSTEM_PROFILE_IDS = new Set([
  'global-socle',
  'eleve',
  'enseignant',
  'technicien',
  'nsi',
  'sciences',
  'multimedia',
])

export default function Profils({ notify, permissions = {} }) {
  const [profiles, setProfiles] = useState([])
  const [assignments, setAssignments] = useState([])
  const [themes, setThemes] = useState([])
  const [approvedPackages, setApprovedPackages] = useState([])
  const [auditLog, setAuditLog] = useState([])

  // Données réelles pour les sélecteurs d'affectation
  const [roles, setRoles] = useState([])
  const [classes, setClasses] = useState([])
  const [users, setUsers] = useState([])
  const [machines, setMachines] = useState([])

  const [selectedId, setSelectedId] = useState('')
  const [editName, setEditName] = useState('')
  const [editTheme, setEditTheme] = useState('lyux-ocean')
  const [editPackages, setEditPackages] = useState([])
  const [editKiosk, setEditKiosk] = useState(false)
  const [pkgSearch, setPkgSearch] = useState('')
  const [preview, setPreview] = useState(null)
  const [pilotTarget, setPilotTarget] = useState('')
  const [assignType, setAssignType] = useState('role')
  const [assignTarget, setAssignTarget] = useState('')
  const [saving, setSaving] = useState(false)

  // Modale création de profil
  const [showNewModal, setShowNewModal] = useState(false)
  const [newId, setNewId] = useState('')
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [newScope, setNewScope] = useState('group')

  const canManage = permissions['profiles.manage'] !== false

  const loadProfiles = useCallback(() => {
    api.getProfiles()
      .then((res) => {
        const list = Array.isArray(res?.profiles) ? res.profiles : []
        setProfiles(list)
        setAssignments(Array.isArray(res?.assignments) ? res.assignments : [])
        setThemes(Array.isArray(res?.approved_themes) ? res.approved_themes : [])
        setApprovedPackages(Array.isArray(res?.approved_packages) ? res.approved_packages : [])
        setAuditLog(Array.isArray(res?.audit_log) ? res.audit_log : [])
        if (list.length > 0) {
          setSelectedId((prev) => (list.some((p) => p.id === prev) ? prev : list[0].id))
        }
      })
      .catch((err) => notify(err.message || 'Erreur lors du chargement des profils.', 'danger'))
  }, [notify])

  useEffect(() => {
    loadProfiles()
    api.getRoles().then((r) => Array.isArray(r?.roles) && setRoles(r.roles)).catch(() => {})
    api.getClasses().then((c) => setClasses(Array.isArray(c) ? c : Object.values(c || {}))).catch(() => {})
    api.getUsers().then((u) => Array.isArray(u) && setUsers(u)).catch(() => {})
    api.getMachines().then((m) => {
      if (Array.isArray(m)) {
        setMachines(m)
        if (m.length > 0) setPilotTarget((prev) => prev || m[0].hostname)
      }
    }).catch(() => {})
  }, [loadProfiles])

  const selected = profiles.find((p) => p.id === selectedId) || null

  useEffect(() => {
    if (selected) {
      setEditName(selected.name || selected.id)
      setEditTheme(selected.desktop_theme || 'lyux-ocean')
      setEditPackages(Array.isArray(selected.packages) ? selected.packages : [])
      setEditKiosk(Boolean(selected.kiosk_locked))
      setPreview(null)
    }
  }, [selected?.id, selected?.name, selected?.desktop_theme, selected?.kiosk_locked])

  const targetOptions = useMemo(() => {
    if (assignType === 'global') return [{ value: '*', label: 'Tout le lycée (*)' }]
    if (assignType === 'role') return roles.map((r) => ({ value: r.id, label: r.name }))
    if (assignType === 'group') return classes.map((c) => ({ value: c.id, label: `${c.id}${c.name ? ` — ${c.name}` : ''}` }))
    if (assignType === 'user') return users.map((u) => ({ value: u.username, label: `${u.display_name || u.username} (${u.username})` }))
    if (assignType === 'machine') return machines.map((m) => ({ value: m.hostname, label: `${m.hostname} (${m.ip || m.room || '—'})` }))
    return []
  }, [assignType, roles, classes, users, machines])

  useEffect(() => {
    if (targetOptions.length > 0 && !targetOptions.some((o) => o.value === assignTarget)) {
      setAssignTarget(targetOptions[0].value)
    } else if (targetOptions.length === 0) {
      setAssignTarget('')
    }
  }, [targetOptions, assignTarget])

  const filteredPackages = useMemo(() => {
    const q = pkgSearch.trim().toLowerCase()
    return approvedPackages.filter((pkg) => !q || pkg.toLowerCase().includes(q))
  }, [approvedPackages, pkgSearch])

  const togglePackage = (pkg) => {
    if (!canManage) return
    setEditPackages((prev) => (prev.includes(pkg) ? prev.filter((p) => p !== pkg) : [...prev, pkg]))
  }

  const handlePreview = async () => {
    if (!selected) return
    try {
      const res = await api.previewProfile({
        profile_id: selected.id,
        desktop_theme: editTheme,
        packages: editPackages,
        kiosk_locked: editKiosk,
        target_type: selected.scope || 'global',
        target_id: selected.id,
      })
      setPreview(res)
    } catch (err) {
      notify(err.message || 'Erreur lors de la prévisualisation.', 'danger')
    }
  }

  const handleSave = async () => {
    if (!selected || !canManage) return
    setSaving(true)
    try {
      await api.saveProfile({
        id: selected.id,
        name: editName.trim() || selected.id,
        description: selected.description || '',
        scope: selected.scope || 'global',
        kiosk_locked: editKiosk,
        packages: editPackages,
        desktop_theme: editTheme,
      })
      notify(`Profil « ${editName.trim() || selected.name} » publié.`, 'success')
      loadProfiles()
    } catch (err) {
      notify(err.message || 'Erreur lors de la publication.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  const handleCreateProfile = async () => {
    const pid = newId.trim().toLowerCase().replace(/[^a-z0-9-_]/g, '-')
    if (!pid || !newName.trim()) {
      notify('Renseignez un identifiant et un nom de profil.', 'warning')
      return
    }
    try {
      await api.saveProfile({
        id: pid,
        name: newName.trim(),
        description: newDesc.trim(),
        scope: newScope,
        kiosk_locked: false,
        packages: ['firefox-esr'],
        desktop_theme: 'lyux-ocean',
      })
      notify(`Profil « ${newName.trim()} » créé.`, 'success')
      setShowNewModal(false)
      setNewId('')
      setNewName('')
      setNewDesc('')
      setSelectedId(pid)
      loadProfiles()
    } catch (err) {
      notify(err.message || 'Erreur lors de la création du profil.', 'danger')
    }
  }

  const handleDeleteProfile = async (prof) => {
    if (!canManage || SYSTEM_PROFILE_IDS.has(prof.id)) return
    try {
      await api.deleteProfile(prof.id)
      notify(`Profil « ${prof.name} » supprimé.`, 'info')
      loadProfiles()
    } catch (err) {
      notify(err.message || 'Impossible de supprimer ce profil.', 'danger')
    }
  }

  const handlePilot = async () => {
    if (!selected || !canManage || !pilotTarget.trim()) return
    try {
      await api.pilotProfile({
        profile_id: selected.id,
        target_type: 'machine',
        target_id: pilotTarget.trim(),
      })
      notify(`Profil « ${selected.name} » appliqué sur le poste pilote ${pilotTarget.trim()}.`, 'success')
      loadProfiles()
    } catch (err) {
      notify(err.message || 'Erreur lors de l’application pilote.', 'danger')
    }
  }

  const handleReset = async () => {
    if (!selected || !canManage) return
    try {
      await api.resetProfile(selected.id)
      notify(`Profil « ${selected.name} » restauré aux valeurs par défaut LyuX.`, 'info')
      loadProfiles()
    } catch (err) {
      notify(err.message || 'Impossible de réinitialiser ce profil.', 'danger')
    }
  }

  const handleAssign = async () => {
    if (!selected || !canManage || !assignTarget) return
    try {
      await api.assignProfile({
        target_type: assignType,
        target_id: assignTarget,
        profile_id: selected.id,
      })
      notify(`Profil « ${selected.name} » affecté à ${SCOPE_LABELS[assignType]} : ${assignTarget}.`, 'success')
      loadProfiles()
    } catch (err) {
      notify(err.message || 'Erreur lors de l’affectation.', 'danger')
    }
  }

  const handleUnassign = async (assignment) => {
    if (!canManage) return
    try {
      await api.unassignProfile(assignment)
      notify(`Affectation ${assignment.target_id} retirée.`, 'info')
      loadProfiles()
    } catch (err) {
      notify(err.message || 'Impossible de retirer cette affectation.', 'danger')
    }
  }

  return (
    <>
      <PageActions>
        {canManage && (
          <Button icon="plus" onClick={() => setShowNewModal(true)}>Nouveau profil</Button>
        )}
        <Button icon="eye" onClick={handlePreview} disabled={!selected}>Prévisualiser l’impact</Button>
        {canManage && selected && SYSTEM_PROFILE_IDS.has(selected.id) && (
          <Button icon="refresh" onClick={handleReset}>Revenir par défaut</Button>
        )}
        {canManage && selected && (
          <Button variant="primary" icon="save" disabled={saving} onClick={handleSave}>
            Publier le profil
          </Button>
        )}
      </PageActions>

      <div className="grid-1-2">
        <Card title="Profils globaux lycée" subtitle={`${profiles.length} profil(s) · valables dans tout l’établissement`}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {profiles.map((prof) => {
              const active = prof.id === selectedId
              const swatch = THEME_SWATCHES[prof.desktop_theme] || '#0284c7'
              return (
                <div
                  key={prof.id}
                  role="button"
                  tabIndex={0}
                  onClick={() => setSelectedId(prof.id)}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelectedId(prof.id) } }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 10,
                    padding: '10px 12px',
                    borderRadius: 6,
                    cursor: 'pointer',
                    border: active ? '1px solid var(--brand)' : '1px solid var(--border)',
                    background: active ? 'rgba(2, 132, 199, 0.08)' : 'transparent',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                    <span style={{ width: 12, height: 12, borderRadius: 3, background: swatch, flexShrink: 0, border: '1px solid rgba(0,0,0,.15)' }} />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{prof.name}</div>
                      <small className="muted">{(prof.packages || []).length} paquet(s) · {prof.kiosk_locked ? 'Kiosk' : 'Standard'}</small>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }} onClick={(e) => e.stopPropagation()}>
                    <Badge tone="brand">{SCOPE_LABELS[prof.scope] || prof.scope}</Badge>
                    {canManage && !SYSTEM_PROFILE_IDS.has(prof.id) && (
                      <IconButton icon="trash" label={`Supprimer ${prof.name}`} onClick={() => handleDeleteProfile(prof)} />
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        <Card
          title={selected ? `Configuration — ${selected.name}` : 'Sélectionnez un profil'}
          subtitle={selected?.description || 'Catalogue signé uniquement (aucun script ni URL libre)'}
        >
          {selected && (
            <div className="form-stack">
              <div className="form-grid">
                <FormField label="Nom affiché">
                  <input value={editName} disabled={!canManage} onChange={(e) => setEditName(e.target.value)} />
                </FormField>
                <FormField label="Thème KDE approuvé">
                  <Select
                    value={editTheme}
                    onChange={setEditTheme}
                    options={themes.map((t) => ({ value: t.id, label: t.name }))}
                  />
                </FormField>
              </div>

              <FormField label="Mode d’exécution">
                <div className="inline-toggle">
                  <Toggle checked={editKiosk} onChange={setEditKiosk} label="Verrouillage Kiosk" />
                  <span>{editKiosk ? 'Bureau verrouillé (mode élève Kiosk)' : 'Bureau complet standard'}</span>
                </div>
              </FormField>

              <FormField label={`Applications du catalogue signé (${editPackages.length} sélectionnée(s))`}>
                <input
                  value={pkgSearch}
                  onChange={(e) => setPkgSearch(e.target.value)}
                  placeholder="Filtrer les paquets (ex. thonny, veyon, gimp)…"
                  style={{ marginBottom: 8 }}
                />
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {filteredPackages.map((pkg) => {
                    const checked = editPackages.includes(pkg)
                    return (
                      <button
                        key={pkg}
                        type="button"
                        disabled={!canManage}
                        onClick={() => togglePackage(pkg)}
                        className={`btn btn-sm ${checked ? 'btn-primary' : ''}`}
                        style={{ fontFamily: 'monospace', fontSize: 12 }}
                      >
                        {checked ? '✓ ' : '+ '}{pkg}
                      </button>
                    )
                  })}
                </div>
              </FormField>

              {preview && (
                <div className="note-box" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
                  <strong>Portée estimée : {preview.scope_label}</strong>
                  <span>
                    {preview.affected_count} cible(s) · Thème : <code>{preview.desktop_theme}</code> · {preview.packages.length} paquet(s) · {preview.kiosk_locked ? 'Kiosk verrouillé' : 'Standard'}
                  </span>
                </div>
              )}

              {canManage && machines.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>Test pilote :</span>
                  <Select
                    value={pilotTarget}
                    onChange={setPilotTarget}
                    options={machines.map((m) => ({ value: m.hostname, label: `${m.hostname} (${m.ip || '—'})` }))}
                  />
                  <Button size="sm" icon="monitor" onClick={handlePilot}>Appliquer sur ce poste pilote</Button>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      <div className="grid-1-1" style={{ marginTop: 16 }}>
        <Card title="Affectations actives" subtitle="Couches : global → établissement → rôle → classe → utilisateur → poste">
          {canManage && selected && (
            <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap', alignItems: 'center' }}>
              <Select
                value={assignType}
                onChange={setAssignType}
                options={[
                  { value: 'global', label: 'Tout le lycée' },
                  { value: 'role', label: 'Rôle' },
                  { value: 'group', label: 'Classe / Groupe' },
                  { value: 'user', label: 'Utilisateur' },
                  { value: 'machine', label: 'Poste réel' },
                ]}
              />
              <Select
                value={assignTarget}
                onChange={setAssignTarget}
                options={targetOptions.length > 0 ? targetOptions : [{ value: '', label: 'Aucune cible disponible' }]}
              />
              <Button size="sm" variant="primary" disabled={!assignTarget} onClick={handleAssign}>Affecter</Button>
            </div>
          )}
          <div className="stacked">
            {assignments.map((a, idx) => (
              <div className="key-value" key={`${a.target_type}-${a.target_id}-${idx}`}>
                <span className="key-label">
                  <strong>{SCOPE_LABELS[a.target_type] || a.target_type}</strong> · {a.target_id}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Badge tone="brand">{a.profile_id}</Badge>
                  {canManage && a.target_type !== 'global' && (
                    <IconButton icon="trash" label="Retirer l’affectation" onClick={() => handleUnassign(a)} />
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Journal d’audit des profils" subtitle="Modifications, tests pilotes et restaurations">
          {auditLog.length === 0 ? (
            <p className="muted">Aucune modification enregistrée dans cette session.</p>
          ) : (
            <div className="stacked">
              {auditLog.slice(0, 10).map((entry, idx) => (
                <div className="key-value" key={`${entry.timestamp}-${idx}`}>
                  <span className="key-label">{entry.timestamp} · {entry.actor} · <strong>{entry.profile_id}</strong></span>
                  <span className="mono">{entry.detail}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Modal
        open={showNewModal}
        title="Créer un profil global"
        onClose={() => setShowNewModal(false)}
        footer={
          <>
            <Button onClick={() => setShowNewModal(false)}>Annuler</Button>
            <Button variant="primary" icon="check" onClick={handleCreateProfile}>Créer le profil</Button>
          </>
        }
      >
        <div className="form-stack">
          <FormField label="Identifiant technique" hint="Lettres minuscules, chiffres et tirets (ex. labo-svt)">
            <input value={newId} onChange={(e) => setNewId(e.target.value)} placeholder="Ex. labo-svt" />
          </FormField>
          <FormField label="Nom du profil">
            <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Ex. Laboratoire SVT" />
          </FormField>
          <FormField label="Portée par défaut">
            <Select
              value={newScope}
              onChange={setNewScope}
              options={[
                { value: 'group', label: 'Classe / Groupe' },
                { value: 'role', label: 'Rôle' },
                { value: 'user', label: 'Utilisateur' },
                { value: 'machine', label: 'Poste spécifique' },
              ]}
            />
          </FormField>
          <FormField label="Description">
            <textarea rows={2} value={newDesc} onChange={(e) => setNewDesc(e.target.value)} placeholder="Usage pédagogique ou technique…" />
          </FormField>
        </div>
      </Modal>
    </>
  )
}
