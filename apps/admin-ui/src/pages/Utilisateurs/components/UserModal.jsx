import React, { useState } from 'react'
import { Button, FormField, Modal, Select } from '../../../components.jsx'
import { api } from '../../../api/client.js'
import { ROLE_LABELS } from './constants.js'

export default function UserModal({ open, onClose, onCreated, notify }) {
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [role, setRole] = useState('eleve')
  const [classe, setClasse] = useState('')
  const [password, setPassword] = useState('')
  const [saving, setSaving] = useState(false)

  const handleCreate = async () => {
    if (!firstName.trim() || !lastName.trim()) {
      notify('Renseignez le prénom et le nom.', 'warning')
      return
    }
    const cleanPart = (s) => s
      .trim()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
    const username = `${cleanPart(firstName)}.${cleanPart(lastName)}`
    setSaving(true)
    try {
      const res = await api.createUser({
        username,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        role,
        classe: classe.trim() || 'Sans affectation',
        ...(password.trim() ? { password: password.trim() } : {}),
      })
      const pwd = res?.user?.password ? ` (mot de passe : ${res.user.password})` : ''
      notify(`Compte ${username} créé${pwd}.`, 'success')
      setFirstName('')
      setLastName('')
      setRole('eleve')
      setClasse('')
      setPassword('')
      if (onCreated) onCreated()
      onClose()
    } catch (err) {
      notify(err.message || 'Erreur lors de la création du compte.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Créer un utilisateur"
      subtitle="Identifiant généré automatiquement au format prenom.nom."
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Annuler</Button>
          <Button variant="primary" icon="check" disabled={saving} onClick={handleCreate}>Créer le compte</Button>
        </>
      }
    >
      <div className="form-grid">
        <FormField label="Prénom"><input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Ex. Camille" /></FormField>
        <FormField label="Nom"><input value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Ex. Rousseau" /></FormField>
        <FormField label="Rôle principal">
          <Select value={role} onChange={setRole} options={Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))} />
        </FormField>
        <FormField label="Classe"><input value={classe} onChange={(e) => setClasse(e.target.value)} placeholder="Ex. 1G1" /></FormField>
        <FormField label="Mot de passe (optionnel)" hint="Laissez vide pour en générer un automatiquement">
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Saisir un mot de passe" />
        </FormField>
      </div>
    </Modal>
  )
}
