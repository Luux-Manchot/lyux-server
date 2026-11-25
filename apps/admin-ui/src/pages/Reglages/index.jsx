import React, { useEffect, useState } from 'react'
import { Button, PageActions, Tabs } from '../../components.jsx'
import { api } from '../../api/client.js'
import GeneralTab from './components/GeneralTab.jsx'
import UpdatesTab from './components/UpdatesTab.jsx'
import SecurityTab from './components/SecurityTab.jsx'
import './Reglages.css'

const DEFAULT_FORM_SETTINGS = {
  schoolName: 'Lycée Opération Manchot',
  schoolYear: '2026 – 2027',
  contact: 'administration@lyux.lan',
  timezone: 'Europe/Paris',
  enrollment: true,
  autoUpdate: true,
  updateWindow: '22:00 – 05:00',
  channel: 'stable',
  retentionDays: '30',
}

export default function Reglages({ notify }) {
  const [tab, setTab] = useState('general')
  const [form, setForm] = useState(DEFAULT_FORM_SETTINGS)
  const [maintenance, setMaintenance] = useState(false)

  useEffect(() => {
    Promise.all([
      api.getSettings().catch(() => null),
      api.getSetup().catch(() => null),
    ]).then(([sys, setup]) => {
      setForm((prev) => ({
        ...prev,
        ...(setup ? {
          schoolName: setup.school_name || prev.schoolName,
          schoolYear: setup.school_year || prev.schoolYear,
          contact: setup.admin_email || prev.contact,
          timezone: setup.timezone || prev.timezone,
          updateWindow: setup.update_window || prev.updateWindow,
        } : {}),
        ...(sys ? {
          enrollment: sys.enrollment_enabled ?? prev.enrollment,
          autoUpdate: sys.auto_update_clients ?? prev.autoUpdate,
        } : {}),
      }))
    })
  }, [])

  const set = (key) => (value) => setForm((previous) => ({ ...previous, [key]: value }))

  const handleSave = async () => {
    try {
      await api.saveSettings({
        enrollment_enabled: form.enrollment,
        auto_update_clients: form.autoUpdate,
      })
      notify('Paramètres enregistrés sur le serveur.', 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors de la sauvegarde.', 'danger')
    }
  }

  return (
    <>
      <PageActions>
        <Button icon="refresh" onClick={() => { setForm(DEFAULT_FORM_SETTINGS); notify('Valeurs réinitialisées.', 'info') }}>Réinitialiser</Button>
        <Button variant="primary" icon="save" onClick={handleSave}>Enregistrer</Button>
      </PageActions>

      <Tabs
        tabs={[
          { id: 'general', label: 'Général', icon: 'settings' },
          { id: 'mises-a-jour', label: 'Mises à jour', icon: 'download' },
          { id: 'securite', label: 'Sécurité', icon: 'shield' },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === 'general' && <GeneralTab form={form} set={set} />}
      {tab === 'mises-a-jour' && <UpdatesTab form={form} set={set} />}
      {tab === 'securite' && (
        <SecurityTab
          form={form}
          set={set}
          notify={notify}
          maintenance={maintenance}
          setMaintenance={setMaintenance}
        />
      )}
    </>
  )
}
