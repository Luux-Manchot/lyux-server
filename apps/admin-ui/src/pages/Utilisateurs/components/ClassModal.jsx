import React, { useState } from 'react'
import { Button, FormField, Modal, Select } from '../../../components.jsx'
import { api } from '../../../api/client.js'

export default function ClassModal({ open, onClose, onCreated, notify }) {
  const [id, setId] = useState('')
  const [name, setName] = useState('')
  const [level, setLevel] = useState('2nde')
  const [saving, setSaving] = useState(false)

  const handleCreate = async () => {
    const cid = id.trim().toUpperCase()
    if (!cid) {
      notify('Renseignez un identifiant de classe.', 'warning')
      return
    }
    setSaving(true)
    try {
      await api.createClass({ id: cid, name: name.trim() || cid, level })
      notify(`Classe ${cid} créée.`, 'success')
      setId('')
      setName('')
      if (onCreated) onCreated()
      onClose()
    } catch (err) {
      notify(err.message || 'Erreur lors de la création de la classe.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Créer une classe"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Annuler</Button>
          <Button variant="primary" icon="check" disabled={saving} onClick={handleCreate}>Créer la classe</Button>
        </>
      }
    >
      <div className="form-stack">
        <FormField label="Identifiant classe" hint="Ex. 2NDE1, TG2.">
          <input value={id} onChange={(e) => setId(e.target.value)} placeholder="Ex. 2NDE1" />
        </FormField>
        <FormField label="Nom complet"><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex. Seconde 1 Générale" /></FormField>
        <FormField label="Niveau">
          <Select value={level} onChange={setLevel} options={[{ value: '2nde', label: 'Seconde' }, { value: '1ere', label: 'Première' }, { value: 'terminale', label: 'Terminale' }]} />
        </FormField>
      </div>
    </Modal>
  )
}
