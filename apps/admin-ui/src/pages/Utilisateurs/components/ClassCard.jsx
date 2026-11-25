import React from 'react'
import { Badge, Button, Card, IconButton } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function ClassCard({ item, notify }) {
  return (
    <Card
      title={`${item.id} — ${item.name}`}
      subtitle={`${item.level} · salle ${item.room}`}
      actions={<Badge tone="brand">{item.students} élèves</Badge>}
    >
      <div className="class-section">
        <span className="class-label">Sous-groupes de TP</span>
        <div className="chips">
          {item.subgroups.map((group) => <span className="chip" key={group}>{group}</span>)}
        </div>
      </div>
      <div className="class-section">
        <span className="class-label">Équipe pédagogique</span>
        <div className="chips">
          {item.teachers.map((teacher) => <Badge tone="success" key={teacher}>{teacher}</Badge>)}
        </div>
      </div>
      <div className="share-grid">
        <div><Icon name="folder" size={15} /><span><strong>Dossier Cours</strong><small>Enseignants R/W · élèves lecture</small></span></div>
        <div><Icon name="folder" size={15} /><span><strong>Dépôt devoirs</strong><small>Boîte aux lettres étanche</small></span></div>
      </div>
      <div className="card-footer-actions">
        <Button size="sm" icon="folder" onClick={() => notify(`Partage Samba : \\\\serveur.lyux.lan\\classes\\${item.id}`, 'info')}>Partages Samba</Button>
      </div>
    </Card>
  )
}
