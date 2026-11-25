import React, { useEffect, useState } from 'react'
import { Avatar, Badge, Button, Card, KeyValue, Select, StatCard, Toolbar } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'
import { api } from '../../../api/client.js'
import { ROLE_LABELS, ROLE_TONES } from './constants.js'

function generateRandomPassword(length = 12) {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#%'
  let out = ''
  for (let i = 0; i < length; i += 1) {
    out += chars[Math.floor(Math.random() * chars.length)]
  }
  return out
}

export default function UsersPanel({
  notify,
  search,
  onSearch,
  roleFilter,
  onRoleFilterChange,
  rows,
  allUsers = [],
  classes = [],
  machines = [],
  canManage = true,
  onUserUpdated,
  onAddUser,
}) {
  const [selectedUsername, setSelectedUsername] = useState(null)
  const [editName, setEditName] = useState('')
  const [editRoles, setEditRoles] = useState(['eleve'])
  const [editClasse, setEditClasse] = useState('')
  const [newGroup, setNewGroup] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [saving, setSaving] = useState(false)

  const selected = rows.find((u) => u.username === selectedUsername) || rows[0] || null

  useEffect(() => {
    if (selected) {
      setEditName(selected.displayName || '')
      setEditRoles(Array.isArray(selected.roles) && selected.roles.length > 0 ? selected.roles : [selected.role || 'eleve'])
      setEditClasse(selected.classe === '—' ? '' : (selected.classe || ''))
      setNewPassword('')
      setNewGroup('')
    }
  }, [selected?.username, selected?.displayName, selected?.role, selected?.classe])

  const lastMachine = selected
    ? machines.find((m) => (m.user || '').toLowerCase() === selected.username.toLowerCase())
    : null

  const groups = selected
    ? (Array.isArray(selected.groups) && selected.groups.length > 0
      ? selected.groups
      : (selected.classe && selected.classe !== '—' ? [selected.classe] : []))
    : []

  const toggleEditRole = (roleId) => {
    setEditRoles((prev) => {
      if (prev.includes(roleId)) {
        const next = prev.filter((r) => r !== roleId)
        return next.length > 0 ? next : prev
      }
      return [...prev, roleId]
    })
  }

  const handleSaveIdentity = async () => {
    if (!selected || !canManage) return
    setSaving(true)
    try {
      await api.updateUser(selected.username, {
        display_name: editName.trim() || selected.username,
        roles: editRoles,
        classe: editClasse.trim(),
      })
      notify(`Profil de ${selected.username} mis à jour.`, 'success')
      if (onUserUpdated) onUserUpdated()
    } catch (err) {
      notify(err.message || 'Erreur lors de la mise à jour.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  const handleAddGroup = async () => {
    const g = newGroup.trim()
    if (!selected || !g) return
    if (groups.includes(g)) {
      notify('Ce groupe est déjà attribué.', 'warning')
      return
    }
    const nextGroups = [...groups, g]
    try {
      await api.updateUser(selected.username, { groups: nextGroups })
      setNewGroup('')
      notify(`Groupe « ${g} » ajouté à ${selected.username}.`, 'success')
      if (onUserUpdated) onUserUpdated()
    } catch (err) {
      notify(err.message || 'Erreur lors de l’ajout du groupe.', 'danger')
    }
  }

  const handleRemoveGroup = async (groupName) => {
    if (!selected) return
    const nextGroups = groups.filter((g) => g !== groupName)
    try {
      await api.updateUser(selected.username, { groups: nextGroups })
      notify(`Groupe « ${groupName} » retiré.`, 'info')
      if (onUserUpdated) onUserUpdated()
    } catch (err) {
      notify(err.message || 'Erreur lors du retrait du groupe.', 'danger')
    }
  }

  const handleResetPassword = async () => {
    if (!selected) return
    const pwd = newPassword.trim()
    if (pwd.length < 6) {
      notify('Saisissez ou générez un mot de passe d’au moins 6 caractères.', 'warning')
      return
    }
    setSaving(true)
    try {
      await api.resetPassword(selected.username, pwd)
      notify(`Mot de passe mis à jour pour ${selected.username}.`, 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors de la réinitialisation du mot de passe.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleStatus = async () => {
    if (!selected) return
    const nextStatus = selected.status === 'active' ? 'disabled' : 'active'
    try {
      await api.updateUser(selected.username, { status: nextStatus })
      notify(`Compte ${selected.username} ${nextStatus === 'active' ? 'activé' : 'désactivé'}.`, 'info')
      if (onUserUpdated) onUserUpdated()
    } catch (err) {
      notify(err.message || 'Erreur lors du changement de statut.', 'danger')
    }
  }

  return (
    <>
      <div className="stat-grid four">
        <StatCard icon="users" label="Comptes actifs" value={allUsers.filter((user) => user.status === 'active').length} tone="success" />
        <StatCard icon="graduation" label="Élèves" value={allUsers.filter((user) => user.role === 'eleve').length} tone="brand" />
        <StatCard icon="briefcase" label="Personnels" value={allUsers.filter((user) => user.role !== 'eleve').length} tone="violet" />
        <StatCard icon="key" label="Total comptes" value={allUsers.length} tone="neutral" />
      </div>

      <div className="users-split">
        <Card
          title="Comptes"
          subtitle={`${rows.length} affiché(s)`}
          actions={onAddUser && (
            <Button variant="primary" size="sm" icon="plus" onClick={onAddUser}>
              Ajouter
            </Button>
          )}
        >
          <Toolbar
            search={search}
            onSearch={onSearch}
            placeholder="Rechercher un compte…"
            filters={
              <Select
                label="Rôle"
                value={roleFilter}
                onChange={onRoleFilterChange}
                options={[{ value: 'all', label: 'Tous les rôles' }, ...Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))]}
              />
            }
          />
          <div className="users-list">
            {rows.length === 0 ? (
              <p className="muted" style={{ margin: '8px 0' }}>Aucun compte trouvé.</p>
            ) : (
              rows.map((user) => (
                <button
                  type="button"
                  key={user.id || user.username}
                  className={`user-list-item ${selected?.username === user.username ? 'selected' : ''}`}
                  onClick={() => setSelectedUsername(user.username)}
                >
                  <div className="user-list-meta">
                    <strong>{user.username}</strong>
                    <small>{user.displayName}</small>
                  </div>
                  <Badge tone={ROLE_TONES[user.role] || 'neutral'}>
                    {ROLE_LABELS[user.role] || user.role}
                  </Badge>
                </button>
              ))
            )}
          </div>
        </Card>

        <Card title={selected ? `Fiche compte — ${selected.username}` : 'Fiche compte'} subtitle="Détails, groupes et sécurité">
          {!selected ? (
            <p className="muted">Sélectionnez un utilisateur dans la liste de gauche.</p>
          ) : (
            <>
              <div className="user-detail-head">
                <div className="user-detail-identity">
                  <Avatar name={selected.displayName} tone={ROLE_TONES[selected.role] || 'brand'} />
                  <div>
                    <h4>{selected.displayName}</h4>
                    <small className="mono">{selected.username}</small>
                  </div>
                </div>
                <div className="row-actions">
                  <Badge tone={selected.status === 'active' ? 'success' : 'neutral'} dot>
                    {selected.status === 'active' ? 'Actif' : 'Désactivé'}
                  </Badge>
                  <Button size="sm" onClick={handleToggleStatus}>
                    {selected.status === 'active' ? 'Désactiver' : 'Activer'}
                  </Button>
                </div>
              </div>

              <div className="stacked">
                <KeyValue
                  label="Dernier PC utilisé"
                  value={lastMachine ? `${lastMachine.hostname} (${lastMachine.ip})` : (selected.room && selected.room !== 'ALL' ? `Salle ${selected.room}` : 'Aucun poste actif relevé')}
                  mono={Boolean(lastMachine)}
                />
                <KeyValue label="Application / Profil par défaut" value={selected.app || 'Standard'} />
                <KeyValue label="Synchronisation" value={selected.lastLogin || 'API LyuX'} />
              </div>

              <div className="user-section">
                <p className="user-section-title">Identité & affectation</p>
                <div className="form-grid">
                  <label className="form-field">
                    <span className="form-label">Nom complet</span>
                    <input value={editName} onChange={(e) => setEditName(e.target.value)} />
                  </label>
                  <label className="form-field">
                    <span className="form-label">Rôles attribués (le plus élevé s’applique)</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, paddingTop: 4 }}>
                      {Object.entries(ROLE_LABELS).map(([val, lbl]) => (
                        <label key={val} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12 }}>
                          <input
                            type="checkbox"
                            disabled={!canManage}
                            checked={editRoles.includes(val)}
                            onChange={() => toggleEditRole(val)}
                          />
                          {lbl}
                        </label>
                      ))}
                    </div>
                  </label>
                  <label className="form-field">
                    <span className="form-label">Classe / Service</span>
                    <input
                      value={editClasse}
                      onChange={(e) => setEditClasse(e.target.value)}
                      list="lyux-classes-list"
                      placeholder="ex. 1G1 (B204)"
                    />
                    <datalist id="lyux-classes-list">
                      {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </datalist>
                  </label>
                </div>
                <div style={{ marginTop: 10 }}>
                  <Button variant="primary" size="sm" icon="save" disabled={saving} onClick={handleSaveIdentity}>
                    Enregistrer les modifications
                  </Button>
                </div>
              </div>

              <div className="user-section">
                <p className="user-section-title">Groupes & partages</p>
                <div className="chips" style={{ marginBottom: 8 }}>
                  {groups.length === 0 ? (
                    <span className="muted" style={{ fontSize: 11 }}>Aucun groupe attribué</span>
                  ) : (
                    groups.map((g) => (
                      <span className="group-chip" key={g}>
                        {g}
                        <button type="button" onClick={() => handleRemoveGroup(g)} title="Retirer du groupe">
                          <Icon name="close" size={11} />
                        </button>
                      </span>
                    ))
                  )}
                </div>
                <div className="user-inline-form">
                  <input
                    value={newGroup}
                    onChange={(e) => setNewGroup(e.target.value)}
                    placeholder="Ajouter un groupe (ex. Spé NSI, Profs_Maths)…"
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddGroup() } }}
                  />
                  <Button size="sm" icon="plus" onClick={handleAddGroup}>Ajouter</Button>
                </div>
              </div>

              <div className="user-section">
                <p className="user-section-title">Mot de passe</p>
                <div className="user-inline-form">
                  <input
                    type="text"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Nouveau mot de passe (saisie manuelle ou généré)…"
                  />
                  <Button
                    size="sm"
                    icon="refresh"
                    onClick={() => setNewPassword(generateRandomPassword())}
                  >
                    Aléatoire
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    icon="key"
                    disabled={saving || !newPassword.trim()}
                    onClick={handleResetPassword}
                  >
                    Définir le mot de passe
                  </Button>
                </div>
              </div>
            </>
          )}
        </Card>
      </div>
    </>
  )
}
