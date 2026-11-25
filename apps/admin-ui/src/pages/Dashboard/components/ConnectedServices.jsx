import React from 'react'
import { Badge, Card } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function ConnectedServices({ services, activeCount }) {
  return (
    <Card title="Services connectés" subtitle={`${activeCount} services actifs sur ${services.length}`}>
      <div className="service-list">
        {services.slice(0, 5).map((service) => (
          <div className="service-row" key={service.id}>
            <span className="service-icon"><Icon name={service.category === 'Identité' ? 'shield' : service.category === 'Supervision' ? 'activity' : 'boxes'} size={16} /></span>
            <div>
              <strong>{service.name}</strong>
              <small>{service.detail}</small>
            </div>
            <Badge tone={service.status === 'active' ? 'success' : 'warning'} dot>
              {service.status === 'active' ? 'Actif' : 'Prévu'}
            </Badge>
          </div>
        ))}
      </div>
    </Card>
  )
}
