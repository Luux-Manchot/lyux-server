import React, { useState } from 'react'
import { Button, FormField, Modal } from '../../../components.jsx'
import { api } from '../../../api/client.js'

export default function RoleModal({ open, onClose, onCreated, notify }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState(45)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async () => {
    if (!name.trim()) {
      notify('Saisissez un nom de rôle.', 'warning')
      return
    }
    setSaving(true)
    try {
      await api.createRole({
        name: name.trim(),
        description: description.trim(),
        priority: Number(priority) || 45,
      })
      notify(`Rôle « ${name.trim()} » créé.`, 'success')
      setName('')
      setDescription('')
      setPriority(45)
      if (onCreated) onCreated()
      onClose()
    } catch (err) {
      notify(err.message || 'Erreur lors de la création du rôle.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Créer un rôle"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Annuler</Button>
          <Button variant="primary" icon="check" disabled={saving} onClick={handleSubmit}>Créer le rôle</Button>
        </>
      }
    >
      <div className="form-stack">
        <FormField label="Nom du rôle">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex. Agent de laboratoire" />
        </FormField>
        <FormField label="Priorité (1 – 99)">
          <input type="number" min={1} max={99} value={priority} onChange={(e) => setPriority(e.target.value)} />
        </FormField>
        <FormField label="Description">
          <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Décrivez le périmètre de ce rôle…" />
        </FormField>
      </div>
    </Modal>
  )
}
