import React from 'react'
import { Button, FormField, Modal, Select } from '../../../components.jsx'

export default function RoomModal({
  open,
  name,
  onNameChange,
  buildingId,
  onBuildingChange,
  buildings,
  onClose,
  onCreate,
}) {
  return (
    <Modal
      open={open}
      title="Créer une salle"
      subtitle="La salle sera rattachée au bâtiment sélectionné."
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Annuler</Button>
          <Button variant="primary" icon="check" onClick={onCreate}>Créer la salle</Button>
        </>
      }
    >
      <div className="form-stack">
        <FormField label="Nom de la salle" hint="Identifiant unique dans le bâtiment, ex. C15.">
          <input value={name} onChange={(event) => onNameChange(event.target.value)} placeholder="Ex. C15" />
        </FormField>
        <FormField label="Bâtiment de rattachement">
          <Select value={buildingId} onChange={onBuildingChange} options={buildings.map((building) => ({ value: building.id, label: building.name }))} />
        </FormField>
        <FormField label="Capacité maximale">
          <input type="number" defaultValue={24} min={1} max={100} />
        </FormField>
      </div>
    </Modal>
  )
}
