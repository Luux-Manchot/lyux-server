import React from 'react'
import { Button, FormField, Modal } from '../../../components.jsx'

export default function BuildingModal({ open, name, onNameChange, onClose, onCreate }) {
  return (
    <Modal
      open={open}
      title="Créer un bâtiment"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Annuler</Button>
          <Button variant="primary" icon="check" onClick={onCreate}>Créer le bâtiment</Button>
        </>
      }
    >
      <FormField label="Nom du bâtiment" hint="Ex. Bâtiment H.">
        <input value={name} onChange={(event) => onNameChange(event.target.value)} placeholder="Ex. Bâtiment H" />
      </FormField>
    </Modal>
  )
}
