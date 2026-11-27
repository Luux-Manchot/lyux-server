import React, { useEffect, useState } from 'react'
import { Button, Card, EmptyState, Select, Toolbar } from '../../../components.jsx'
import SoftwareInfo from './SoftwareInfo.jsx'

// La liste de gauche ne contient que le nom des applications : aucun bouton,
// aucune colonne supplémentaire. La fiche de droite affiche les informations.
export default function SoftwarePanel({ notify, search, onSearch, category, onCategoryChange, categories, rows, focusId, onUpdated, onDeleted }) {
  const [selectedId, setSelectedId] = useState(rows[0]?.id || null)

  // Un logiciel ajouté pendant la session devient immédiatement la sélection.
  useEffect(() => {
    if (focusId) setSelectedId(focusId)
  }, [focusId])

  // Si un filtre masque l'application sélectionnée, on passe à la première
  // application visible ; c'est aussi la sélection par défaut de la page.
  useEffect(() => {
    if (!rows.some((app) => app.id === selectedId)) {
      setSelectedId(rows[0]?.id || null)
    }
  }, [rows, selectedId])

  const selectedApp = rows.find((app) => app.id === selectedId) || rows[0] || null

  return (
    <Card
      title="Catalogue applicatif"
      subtitle="Sélectionnez une application pour consulter sa fiche"
      actions={<Button size="sm" icon="refresh" onClick={() => window.location.reload()}>Actualiser</Button>}
    >
      <Toolbar
        search={search}
        onSearch={onSearch}
        placeholder="Rechercher une application…"
        filters={
          <Select
            label="Catégorie"
            value={category}
            onChange={onCategoryChange}
            options={categories.map((item) => ({ value: item, label: item === 'all' ? 'Toutes les catégories' : item }))}
          />
        }
      />

      <div className="software-layout">
        {rows.length === 0 ? (
          <EmptyState
            icon="search"
            title="Aucune application"
            description="Aucune application ne correspond à cette recherche."
            compact
          />
        ) : (
          <div className="software-picker" role="listbox" aria-label="Applications du catalogue">
            {rows.map((app) => {
              const isSelected = app.id === selectedApp?.id
              return (
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`software-item ${isSelected ? 'selected' : ''}`}
                  key={app.id}
                  onClick={() => setSelectedId(app.id)}
                >
                  {app.name}
                </button>
              )
            })}
          </div>
        )}

        <SoftwareInfo app={selectedApp} notify={notify} onUpdated={onUpdated} onDeleted={onDeleted} />
      </div>
    </Card>
  )
}
