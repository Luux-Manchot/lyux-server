import React from 'react'
import { Avatar, Badge, Card, DataTable, IconButton, Select, StatCard, Toolbar } from '../../../components.jsx'
import { ROLE_LABELS, ROLE_TONES } from './constants.js'

export default function UsersPanel({ notify, search, onSearch, roleFilter, onRoleFilterChange, rows, allUsers = [] }) {
  return (
    <>
      <div className="stat-grid four">
        <StatCard icon="users" label="Comptes actifs" value={allUsers.filter((user) => user.status === 'active').length} tone="success" />
        <StatCard icon="graduation" label="Élèves" value={allUsers.filter((user) => user.role === 'eleve').length} tone="brand" />
        <StatCard icon="briefcase" label="Personnels" value={allUsers.filter((user) => user.role !== 'eleve').length} tone="violet" />
        <StatCard icon="key" label="Total comptes" value={allUsers.length} tone="neutral" />
      </div>

      <Card title="Comptes utilisateurs" subtitle="Gestion des identités et des affectations">
        <Toolbar
          search={search}
          onSearch={onSearch}
          placeholder="Rechercher un nom ou un identifiant…"
          filters={
            <Select
              label="Rôle"
              value={roleFilter}
              onChange={onRoleFilterChange}
              options={[{ value: 'all', label: 'Tous les rôles' }, ...Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))]}
            />
          }
        />
        <DataTable
          columns={[
            {
              key: 'displayName',
              label: 'Utilisateur',
              render: (user) => (
                <div className="person-cell">
                  <Avatar name={user.displayName} tone={ROLE_TONES[user.role]} />
                  <span><strong>{user.displayName}</strong><small className="mono">{user.username}</small></span>
                </div>
              ),
            },
            { key: 'role', label: 'Rôle', render: (user) => <Badge tone={ROLE_TONES[user.role]}>{ROLE_LABELS[user.role]}</Badge> },
            { key: 'classe', label: 'Classe', render: (user) => user.classe === '—' ? <span className="muted">—</span> : <strong>{user.classe}</strong> },
            { key: 'group', label: 'Groupe / matière' },
            { key: 'status', label: 'Statut', render: (user) => <Badge tone={user.status === 'active' ? 'success' : 'neutral'} dot>{user.status === 'active' ? 'Actif' : 'Désactivé'}</Badge> },
            { key: 'lastLogin', label: 'Dernière connexion', render: (user) => <span className="muted">{user.lastLogin}</span> },
            {
              key: 'actions',
              label: 'Actions',
              align: 'right',
              render: (user) => (
                <div className="row-actions">
                  <IconButton icon="pencil" label={`Modifier ${user.username}`} onClick={() => notify('Modification simulée.', 'info')} />
                  <IconButton icon="key" label={`Réinitialiser le mot de passe de ${user.username}`} onClick={() => notify(`Mot de passe de ${user.username} réinitialisé (simulation).`, 'success')} />
                  <IconButton icon="trash" label={`Supprimer ${user.username}`} onClick={() => notify('Suppression simulée.', 'warning')} />
                </div>
              ),
            },
          ]}
          rows={rows}
        />
      </Card>
    </>
  )
}
