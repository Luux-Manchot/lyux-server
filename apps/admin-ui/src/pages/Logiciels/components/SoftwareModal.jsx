import React, { useState } from 'react'
import { Button, FormField, Modal, Select } from '../../../components.jsx'

const SOURCES = [
  { value: 'Site officiel', label: 'Site officiel' },
  { value: 'GitHub releases', label: 'GitHub releases' },
  { value: 'Flathub', label: 'Flathub' },
  { value: 'Dépôt Debian', label: 'Dépôt Debian' },
]

const AVAILABLE_ROLES = [
  { id: 'eleve', label: 'Élèves' },
  { id: 'prof', label: 'Enseignants' },
  { id: 'viesco', label: 'Vie scolaire' },
  { id: 'administration', label: 'Administration' },
  { id: 'admin', label: 'Admins' },
]

const SIMULATED_VERSION = '2.1.0'

export default function SoftwareModal({ open, onClose, notify, onAdd, categories = [] }) {
  const initialForm = {
    name: '',
    package: '',
    link: '',
    source: 'Site officiel',
    version: '',
    category: categories[0] || 'Bureautique',
    target: 'Tous les postes',
    allowedRoles: ['eleve', 'prof', 'admin'],
    launchArgs: '',
  }
  const [form, setForm] = useState(initialForm)

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }))
  const toggleRole = (roleId) => {
    setForm((current) => {
      const exists = current.allowedRoles.includes(roleId)
      const next = exists
        ? current.allowedRoles.filter((r) => r !== roleId)
        : [...current.allowedRoles, roleId]
      return { ...current, allowedRoles: next }
    })
  }

  const close = () => {
    setForm({ ...initialForm })
    onClose()
  }

  const checkVersion = () => {
    if (!form.name.trim()) {
      notify('Saisissez d’abord le nom de l’application.', 'warning')
      return
    }
    update('version', SIMULATED_VERSION)
    notify(`Dernière version détectée sur ${form.source} : ${SIMULATED_VERSION} (simulation, aucun appel réseau).`, 'info')
  }

  const submit = () => {
    if (!form.name.trim()) {
      notify('Le nom de l’application est obligatoire.', 'warning')
      return
    }
    onAdd({
      ...form,
      name: form.name.trim(),
      package: form.package.trim(),
      link: form.link.trim(),
      target: form.target.trim() || 'Tous les postes',
      allowedRoles: form.allowedRoles.length ? form.allowedRoles : ['eleve', 'prof', 'admin'],
      version: form.version.trim() || SIMULATED_VERSION,
      launchArgs: form.launchArgs.trim(),
    })
    close()
  }

  return (
    <Modal
      open={open}
      title="Ajouter un logiciel"
      subtitle="Renseignez le point de départ d’une future fiche de catalogue."
      onClose={close}
      width="620px"
      footer={
        <>
          <Button onClick={close}>Annuler</Button>
          <Button variant="primary" icon="check" onClick={submit}>Ajouter au catalogue</Button>
        </>
      }
    >
      <div className="form-stack">
        <FormField label="Nom de l’application">
          <input value={form.name} onChange={(event) => update('name', event.target.value)} placeholder="Ex. Inkscape" />
        </FormField>
        <FormField label="Paquet Debian (.deb)" hint="Nom du paquet apt (laissé vide = déduit du nom).">
          <input value={form.package} onChange={(event) => update('package', event.target.value)} placeholder="Ex. inkscape" />
        </FormField>
        <FormField label="Rôles autorisés" hint="Seuls les rôles cochés verront et pourront lancer cette application.">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', paddingTop: '4px' }}>
            {AVAILABLE_ROLES.map((r) => (
              <label key={r.id} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={form.allowedRoles.includes(r.id)}
                  onChange={() => toggleRole(r.id)}
                />
                <span>{r.label}</span>
              </label>
            ))}
          </div>
        </FormField>
        <FormField label="Lien du logiciel" hint="Adresse du site officiel ou de la page de téléchargement.">
          <input type="url" value={form.link} onChange={(event) => update('link', event.target.value)} placeholder="https://exemple.fr/logiciel" />
        </FormField>
        <FormField label="Source à consulter" hint="Source pressentie pour la détection des versions (non interrogée ici).">
          <Select value={form.source} onChange={(value) => update('source', value)} options={SOURCES.map((item) => ({ value: item.value, label: item.label }))} />
        </FormField>
        <div className="version-check">
          <FormField label="Dernière version connue">
            <input value={form.version} onChange={(event) => update('version', event.target.value)} placeholder="Ex. 2.1.0" />
          </FormField>
          <Button icon="refresh" onClick={checkVersion}>Vérifier</Button>
        </div>
        <FormField label="Catégorie">
          <Select
            value={form.category}
            onChange={(value) => update('category', value)}
            options={categories.map((item) => ({ value: item, label: item }))}
          />
        </FormField>
        <FormField label="Public cible">
          <input value={form.target} onChange={(event) => update('target', event.target.value)} placeholder="Ex. Tous les postes" />
        </FormField>
        <FormField label="Arguments de lancement" hint="Séparés par des espaces, ex. --factory-startup ou wine /opt/app/app.exe.">
          <input value={form.launchArgs} onChange={(event) => update('launchArgs', event.target.value)} placeholder="Ex. --no-splash" />
        </FormField>
      </div>

      <p className="modal-note">
        Prototype visuel : le bouton « Vérifier » renvoie une version simulée et le lien n’est pas
        interrogé. Aucun artefact n’est téléchargé ni installé.
      </p>
    </Modal>
  )
}
