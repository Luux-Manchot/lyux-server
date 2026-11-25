import React from 'react'
import { Card, FormField, Select } from '../../../components.jsx'
import { Icon } from '../../../icons.jsx'

export default function GeneralTab({ form, set }) {
  return (
    <Card title="Établissement" subtitle="Informations affichées dans le panneau et les communications">
      <div className="form-grid">
        <FormField label="Nom de l'établissement">
          <input value={form.schoolName} onChange={(event) => set('schoolName')(event.target.value)} />
        </FormField>
        <FormField label="Année scolaire">
          <input value={form.schoolYear} onChange={(event) => set('schoolYear')(event.target.value)} />
        </FormField>
        <FormField label="Adresse de contact">
          <input value={form.contact} onChange={(event) => set('contact')(event.target.value)} />
        </FormField>
        <FormField label="Fuseau horaire">
          <Select value={form.timezone} onChange={set('timezone')} options={['Europe/Paris', 'Europe/London', 'UTC'].map((value) => ({ value, label: value }))} />
        </FormField>
        <FormField label="Langue de l'interface">
          <Select value={form.language} onChange={set('language')} options={[{ value: 'Français', label: 'Français' }, { value: 'English', label: 'English' }]} />
        </FormField>
      </div>
      <div className="note-box">
        <Icon name="info" size={18} />
        <p>Ces informations sont utilisées dans les en-têtes, les rapports et les notifications envoyées aux utilisateurs.</p>
      </div>
    </Card>
  )
}
