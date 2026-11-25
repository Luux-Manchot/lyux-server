import React from 'react'
import { Button, FormField, Modal, Select } from '../../../components.jsx'
import { ROLE_LABELS } from './constants.js'

export default function UserModal({ open, onClose, notify }) {
  return (
    <Modal
      open={open}
      title="Créer un utilisateur"
      subtitle="Le compte sera rattaché à l'annuaire de l'établissement."
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Annuler</Button>
          <Button variant="primary" icon="check" onClick={() => { onClose(); notify('Utilisateur créé (simulation).', 'success') }}>Créer le compte</Button>
        </>
      }
    >
      <div className="form-grid">
        <FormField label="Prénom"><input placeholder="Ex. Camille" /></FormField>
        <FormField label="Nom"><input placeholder="Ex. Rousseau" /></FormField>
        <FormField label="Rôle">
          <Select value="eleve" onChange={() => {}} options={Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))} />
        </FormField>
        <FormField label="Classe"><input placeholder="Ex. 1G1" /></FormField>
      </div>
    </Modal>
  )
}
