import React from 'react'
import { Button, Card, Timeline } from '../../../components.jsx'

export default function ActivityCard({ items }) {
  return (
    <Card
      title="Activité & Tickets récents"
      subtitle="Derniers événements remontés par l’API"
    >
      {items.length === 0 ? (
        <p className="muted" style={{ margin: 0 }}>Aucune activité enregistrée pour le moment.</p>
      ) : (
        <Timeline items={items} />
      )}
    </Card>
  )
}
