import React from 'react'
import { Badge, Button, Card } from '../../../components.jsx'

export default function RolesPanel({ roles = [], notify, canManage = false, onDeleteRole }) {
  return (
    <div className="role-grid">
      {roles.map((role) => (
        <Card
          key={role.id}
          title={role.name}
          subtitle={role.description}
          actions={
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <Badge tone="neutral">Prio {role.priority ?? 0}</Badge>
              <Badge tone="brand">{role.members ?? 0} membre{(role.members ?? 0) > 1 ? 's' : ''}</Badge>
            </div>
          }
        >
          <div className="card-footer-actions">
            <Button size="sm" icon="eye" onClick={() => notify(`Rôle ${role.name} (priorité ${role.priority ?? 0}) : utilisez la matrice ci-dessous pour ajuster les droits.`, 'info')}>Droits</Button>
            {canManage && !role.system && (
              <Button size="sm" icon="trash" onClick={() => onDeleteRole && onDeleteRole(role)}>
                Supprimer
              </Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}
