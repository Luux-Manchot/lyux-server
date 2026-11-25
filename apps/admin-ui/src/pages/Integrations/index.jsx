import React, { useEffect, useState } from 'react'
import { Button, PageActions, StatCard } from '../../components.jsx'
import { api } from '../../api/client.js'
import './Integrations.css'
import IntegrationGrid from './components/IntegrationGrid.jsx'
import IntegrationNote from './components/IntegrationNote.jsx'
import IntegrationModal from './components/IntegrationModal.jsx'

export default function Integrations({ notify }) {
  const [items, setItems] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [enabled, setEnabled] = useState({})
  const [newType, setNewType] = useState('Supervision')

  useEffect(() => {
    api.health()
      .then((res) => {
        if (Array.isArray(res?.services) && res.services.length > 0) {
          setItems(res.services)
          setEnabled(Object.fromEntries(res.services.map((item) => [item.id, item.status === 'active'])))
        }
      })
      .catch(() => {})
  }, [])

  const activeCount = Object.values(enabled).filter(Boolean).length

  const handleToggle = async (id, name, value) => {
    setEnabled((previous) => ({ ...previous, [id]: value }))
    try {
      await api.saveSettings({ [`module_${id}`]: value })
      notify(`${name} ${value ? 'activé' : 'désactivé'}.`, value ? 'success' : 'warning')
    } catch (err) {
      notify(err.message || 'Erreur lors de la mise à jour du service.', 'danger')
    }
  }

  const handleSubmit = () => {
    setShowModal(false)
    notify(`Intégration ${newType} enregistrée.`, 'success')
  }

  return (
    <>
      <PageActions>
        <Button variant="primary" icon="plus" onClick={() => setShowModal(true)}>Ajouter une intégration</Button>
      </PageActions>

      <div className="stat-grid four">
        <StatCard icon="puzzle" label="Intégrations actives" value={activeCount} tone="success" />
        <StatCard icon="boxes" label="Modules installés" value="6" tone="brand" />
        <StatCard icon="clock" label="Prévus" value="1" tone="warning" />
        <StatCard icon="shield" label="Socle système" value="Cockpit" tone="violet" />
      </div>

      <IntegrationGrid items={items} enabled={enabled} onToggle={handleToggle} notify={notify} />

      <IntegrationNote />

      <IntegrationModal
        open={showModal}
        newType={newType}
        onTypeChange={setNewType}
        onClose={() => setShowModal(false)}
        onSubmit={handleSubmit}
      />
    </>
  )
}
