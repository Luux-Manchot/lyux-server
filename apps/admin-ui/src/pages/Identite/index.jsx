import React, { useEffect, useState } from 'react'
import { Button, PageActions } from '../../components.jsx'
import { api } from '../../api/client.js'
import './Identite.css'
import RolesPanel from './components/RolesPanel.jsx'
import PermissionMatrix from './components/PermissionMatrix.jsx'
import AccountSecurity from './components/AccountSecurity.jsx'
import RoleModal from './components/RoleModal.jsx'

export default function Identite({ notify, permissions = {} }) {
  const [roles, setRoles] = useState([])
  const [matrix, setMatrix] = useState([])
  const [showRoleModal, setShowRoleModal] = useState(false)
  const [twoFactor, setTwoFactor] = useState(true)
  const canManageRoles = permissions['roles.manage'] !== false

  const loadRoles = () => {
    api.getRoles()
      .then((res) => {
        if (Array.isArray(res?.roles)) setRoles(res.roles)
        if (Array.isArray(res?.matrix)) setMatrix(res.matrix)
      })
      .catch((err) => {
        notify(err.message || 'Impossible de charger les rôles.', 'danger')
      })
  }

  useEffect(() => {
    loadRoles()
  }, [])

  const handleTogglePermission = async (rowIdx, roleId) => {
    if (!canManageRoles) {
      notify('Permission roles.manage requise.', 'warning')
      return
    }
    const previous = matrix
    const updated = matrix.map((row, i) => (i === rowIdx ? { ...row, [roleId]: !row[roleId] } : row))
    setMatrix(updated)
    try {
      await api.updatePermissions(updated)
      notify('Matrice des permissions enregistrée.', 'success')
    } catch (err) {
      setMatrix(previous)
      notify(err.message || 'Erreur lors de la mise à jour des permissions.', 'danger')
    }
  }

  const handleDeleteRole = async (role) => {
    if (!canManageRoles || role.system) return
    try {
      await api.deleteRole(role.id)
      notify(`Rôle « ${role.name} » supprimé.`, 'info')
      loadRoles()
    } catch (err) {
      notify(err.message || 'Impossible de supprimer ce rôle.', 'danger')
    }
  }

  return (
    <>
      {canManageRoles && (
        <PageActions>
          <Button variant="primary" icon="plus" onClick={() => setShowRoleModal(true)}>
            Nouveau rôle
          </Button>
        </PageActions>
      )}

      <RolesPanel roles={roles} notify={notify} canManage={canManageRoles} onDeleteRole={handleDeleteRole} />
      <PermissionMatrix roles={roles} matrix={matrix} onToggle={handleTogglePermission} canManage={canManageRoles} />
      <AccountSecurity twoFactor={twoFactor} onTwoFactorChange={setTwoFactor} />

      <RoleModal
        open={showRoleModal}
        onClose={() => setShowRoleModal(false)}
        onCreated={loadRoles}
        notify={notify}
      />
    </>
  )
}
