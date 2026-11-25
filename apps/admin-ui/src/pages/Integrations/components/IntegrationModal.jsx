import React from 'react'
import { Button, FormField, Modal, Select } from '../../../components.jsx'

const CATEGORIES = ['Supervision', 'Identité', 'Inventaire', 'Infrastructure', 'Interface']

export default function IntegrationModal({ open, newType, onTypeChange, onClose, onSubmit }) {
  return (
    <Modal
      open={open}
      title="Ajouter une intégration"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Annuler</Button>
          <Button variant="primary" icon="check" onClick={onSubmit}>Ajouter</Button>
        </>
      }
    >
      <div className="form-stack">
        <FormField label="Nom du service"><input placeholder="Ex. Serveur de sauvegarde" /></FormField>
        <FormField label="Catégorie">
          <Select value={newType} onChange={onTypeChange} options={CATEGORIES.map((value) => ({ value, label: value }))} />
        </FormField>
        <FormField label="Description"><textarea rows={3} placeholder="Rôle du service…" /></FormField>
      </div>
    </Modal>
  )
}
