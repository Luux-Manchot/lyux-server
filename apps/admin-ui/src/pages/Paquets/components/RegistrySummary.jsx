import React from 'react'
import { StatCard } from '../../../components.jsx'

export default function RegistrySummary({ serverVersion, publishedCount, signedCount, draftCount }) {
  return (
    <div className="stat-grid">
      <StatCard icon="server" label="Version serveur" value={serverVersion} hint="Référence du parc" tone="brand" />
      <StatCard icon="package" label="Versions publiées" value={publishedCount} hint="Disponibles pour les postes" tone="success" />
      <StatCard icon="shield" label="Manifests vérifiés" value={signedCount} hint="Signature Ed25519 valide" tone="info" />
      <StatCard icon="boxes" label="Versions en brouillon" value={draftCount} hint="En attente de publication" tone="warning" />
    </div>
  )
}
