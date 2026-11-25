import React, { useEffect, useMemo, useState } from 'react'
import { Button, PageActions, Tabs } from '../../components.jsx'
import { api } from '../../api/client.js'
import './Utilisateurs.css'
import ClassesPanel from './components/ClassesPanel.jsx'
import ClassModal from './components/ClassModal.jsx'
import UsersPanel from './components/UsersPanel.jsx'
import UserModal from './components/UserModal.jsx'

export default function Utilisateurs({ notify, permissions = {} }) {
  const [users, setUsers] = useState([])
  const [classes, setClasses] = useState([])
  const [machines, setMachines] = useState([])
  const [tab, setTab] = useState('users')
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [showUserModal, setShowUserModal] = useState(false)
  const [showClassModal, setShowClassModal] = useState(false)
  const canManageUsers = permissions['users.manage'] !== false

  const loadData = () => {
    api.getUsers()
      .then((list) => {
        if (Array.isArray(list)) {
          setUsers(list.map((u, idx) => ({
            id: u.id || `u-${idx}`,
            username: u.username,
            displayName: u.display_name || u.username,
            role: u.effective_role || u.role || 'eleve',
            roles: Array.isArray(u.roles) && u.roles.length > 0 ? u.roles : [u.effective_role || u.role || 'eleve'],
            group: u.classe || '—',
            classe: u.classe || '—',
            groups: u.groups || [],
            room: u.room || '',
            app: u.app || '',
            status: u.status || 'active',
            lastLogin: 'Synchronisé API',
          })))
        }
      })
      .catch(() => {})
    api.getClasses()
      .then((res) => {
        const list = Array.isArray(res) ? res : Object.values(res || {})
        setClasses(list.map((c) => ({
          ...c,
          room: c.room_default || c.room || '—',
          students: c.students_count ?? c.students ?? 0,
        })))
      })
      .catch(() => {})
    api.getMachines()
      .then((list) => {
        if (Array.isArray(list)) setMachines(list)
      })
      .catch(() => {})
  }

  useEffect(() => {
    loadData()
  }, [])

  const filteredUsers = useMemo(() => {
    const term = search.trim().toLowerCase()
    return users.filter((user) => {
      if (roleFilter !== 'all' && user.role !== roleFilter) return false
      return !term || user.username.includes(term) || user.displayName.toLowerCase().includes(term)
    })
  }, [users, search, roleFilter])

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 14, borderBottom: '1px solid var(--border)' }}>
        <div className="nav nav-tabs tabs" style={{ marginBottom: 0, borderBottom: 0 }}>
          <button
            type="button"
            className={`nav-link tab ${tab === 'users' ? 'active' : ''}`}
            onClick={() => setTab('users')}
          >
            Comptes ({users.length})
          </button>
          <button
            type="button"
            className={`nav-link tab ${tab === 'classes' ? 'active' : ''}`}
            onClick={() => setTab('classes')}
          >
            Classes & groupes ({classes.length})
          </button>
        </div>
        {tab === 'classes' && canManageUsers && (
          <Button variant="primary" size="sm" icon="plus" onClick={() => setShowClassModal(true)}>
            Nouvelle classe
          </Button>
        )}
      </div>

      {tab === 'users' ? (
        <UsersPanel
          notify={notify}
          search={search}
          onSearch={setSearch}
          roleFilter={roleFilter}
          onRoleFilterChange={setRoleFilter}
          rows={filteredUsers}
          allUsers={users}
          classes={classes}
          machines={machines}
          canManage={canManageUsers}
          onUserUpdated={loadData}
          onAddUser={() => setShowUserModal(true)}
        />
      ) : (
        <ClassesPanel classes={classes} notify={notify} />
      )}

      <UserModal open={showUserModal} onClose={() => setShowUserModal(false)} onCreated={loadData} notify={notify} />
      <ClassModal open={showClassModal} onClose={() => setShowClassModal(false)} onCreated={loadData} notify={notify} />
    </>
  )
}
