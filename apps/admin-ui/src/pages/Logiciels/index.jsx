import React, { useEffect, useMemo, useState } from 'react'
import { Button, PageActions } from '../../components.jsx'
import { api } from '../../api/client.js'
import './Logiciels.css'
import SoftwarePanel from './components/SoftwarePanel.jsx'
import SoftwareModal from './components/SoftwareModal.jsx'

const slugify = (value) => value
  .toLowerCase()
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .replace(/[^a-z0-9]+/g, '-')
  .replace(/^-|-$/g, '')

export default function Logiciels({ notify }) {
  const [catalog, setCatalog] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [showAppModal, setShowAppModal] = useState(false)
  const [focusId, setFocusId] = useState(null)

  useEffect(() => {
    api.getApps()
      .then((res) => {
        if (Array.isArray(res)) {
          setCatalog(res.map((a) => ({
            status: 'deployed',
            category: 'Système',
            version: '—',
            target: 'Tous les postes',
            size: '—',
            source: 'Dépôt LyuX',
            format: 'Paquet .deb',
            ...a,
          })))
        }
      })
      .catch(() => {})
  }, [])

  const categories = ['all', ...new Set(catalog.map((app) => app.category))]

  const filteredApps = useMemo(() => {
    const term = search.trim().toLowerCase()
    return catalog.filter((app) => {
      if (category !== 'all' && app.category !== category) return false
      return !term || app.name.toLowerCase().includes(term) || app.version.includes(term)
    })
  }, [catalog, search, category])

  const handleAdd = async (values) => {
    const baseId = slugify(values.name) || 'logiciel'
    let id = baseId
    let suffix = 2
    while (catalog.some((app) => app.id === id)) {
      id = `${baseId}-${suffix++}`
    }

    const payload = {
      id,
      name: values.name,
      category: values.category,
      version: values.version,
      target: values.target,
      source: values.source || 'Dépôt LyuX',
      link: values.link || '',
      launch_args: values.launchArgs || '',
    }

    try {
      const res = await api.addApp(payload)
      const created = res?.app || { ...payload, status: 'pending', launchArgs: values.launchArgs || '' }
      setCatalog((current) => [created, ...current])
      setSearch('')
      setCategory('all')
      setFocusId(created.id)
      notify(`${values.name} ajouté au catalogue serveur.`, 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors de l’ajout du logiciel.', 'danger')
    }
  }

  const handleDeploy = async () => {
    try {
      const res = await api.deployApps()
      notify(res?.message || 'Déploiement applicatif déclenché.', 'success')
    } catch (err) {
      notify(err.message || 'Erreur lors du déploiement.', 'danger')
    }
  }

  return (
    <>
      <PageActions>
        <Button icon="send" onClick={handleDeploy}>
          Déployer sur le parc
        </Button>
        <Button variant="primary" icon="plus" onClick={() => setShowAppModal(true)}>
          Ajouter un logiciel
        </Button>
      </PageActions>

      <SoftwarePanel
        notify={notify}
        search={search}
        onSearch={setSearch}
        category={category}
        onCategoryChange={setCategory}
        categories={categories}
        rows={filteredApps}
        focusId={focusId}
      />

      <SoftwareModal
        open={showAppModal}
        onClose={() => setShowAppModal(false)}
        onAdd={handleAdd}
        notify={notify}
        categories={categories.filter((item) => item !== 'all')}
      />
    </>
  )
}
