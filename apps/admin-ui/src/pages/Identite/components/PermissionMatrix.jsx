import React from 'react'
import { Card } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function PermissionMatrix({ roles = [], matrix = [], onToggle, canManage = true }) {
  return (
    <Card title="Matrice des permissions" subtitle={canManage ? 'Cliquez sur une cellule pour autoriser ou retirer l’accès d’un rôle' : 'Consultation seule (permission roles.manage requise pour modifier)'}>
      <div className="table-wrap">
        <table className="data-table compact-table">
          <thead>
            <tr>
              <th>Fonctionnalité</th>
              {roles.map((role) => <th key={role.id} style={{ textAlign: 'center' }}>{role.name}</th>)}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, rowIdx) => (
              <tr key={row.key || row.feature}>
                <td><strong>{row.feature}</strong></td>
                {roles.map((role) => (
                  <td key={role.id} style={{ textAlign: 'center' }}>
                    <button
                      type="button"
                      className="btn btn-sm"
                      disabled={!canManage}
                      style={{ border: 'none', background: 'transparent', padding: '2px 6px', cursor: canManage ? 'pointer' : 'not-allowed' }}
                      onClick={() => canManage && onToggle && onToggle(rowIdx, role.id)}
                      title={canManage ? `Basculer ${row.feature} pour ${role.name}` : 'Lecture seule'}
                    >
                      {row[role.id]
                        ? <span className="matrix-check"><Icon name="check" size={14} /></span>
                        : <span className="matrix-cross">—</span>}
                    </button>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
