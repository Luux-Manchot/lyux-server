import React from 'react'
import IntegrationCard from './IntegrationCard.jsx'

export default function IntegrationGrid({ items, enabled, onToggle, notify }) {
  return (
    <div className="integration-grid">
      {items.map((item) => (
        <IntegrationCard
          key={item.id}
          item={item}
          enabled={Boolean(enabled[item.id])}
          onToggle={(value) => onToggle(item.id, item.name, value)}
          notify={notify}
        />
      ))}
    </div>
  )
}
