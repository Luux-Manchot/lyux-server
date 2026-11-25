import React from 'react'
import { StatCard } from '../../../components.jsx'
import ClassCard from './ClassCard.jsx'

export default function ClassesPanel({ classes, notify }) {
  return (
    <>
      <div className="stat-grid four">
        <StatCard icon="layers" label="Classes" value={classes.length} tone="brand" />
        <StatCard icon="graduation" label="Élèves inscrits" value={classes.reduce((sum, item) => sum + item.students, 0)} tone="violet" />
        <StatCard icon="briefcase" label="Enseignants" value="2" tone="success" />
        <StatCard icon="users" label="Groupes de TP" value={classes.reduce((sum, item) => sum + item.subgroups.length, 0)} tone="warning" />
      </div>

      <div className="class-grid">
        {classes.map((item) => (
          <ClassCard key={item.id} item={item} notify={notify} />
        ))}
      </div>
    </>
  )
}
