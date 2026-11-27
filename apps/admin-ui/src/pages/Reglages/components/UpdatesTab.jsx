import React, { useEffect, useState } from 'react'
import { Badge, Button, Card, SettingRow, Toggle } from '../../../components.jsx'
import { api } from '../../../api/client.js'
import ServerBuildCard from './ServerBuildCard.jsx'

const COMPONENT_KEYS = [
  { key: 'debian', title: 'Debian', icon: 'server', hint: 'Paquet de référence : base-files' },
  { key: 'kde', title: 'KDE Plasma', icon: 'monitor', hint: 'Paquet de référence : plasma-desktop' },
  { key: 'lyux', title: 'LyuX OS', icon: 'package', hint: 'Paquet de référence : lyux-desktop-core' },
]

export default function UpdatesTab({ form, set, notify }) {
  const [policy, setPolicy] = useState(null)
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.getUpdatesPolicy()
      .then((res) => setPolicy(res?.policy || null))
      .catch(() => setPolicy(null))
      .finally(() => setLoading(false))
  }, [])

  const handleCheckLatest = async () => {
    setChecking(true)
    try {
      const res = await api.checkUpdatesPolicyLatest()
      if (res?.policy) setPolicy(res.policy)
      notify?.('Dernières versions vérifiées depuis les dépôts officiels.', 'success')
    } catch (err) {
      notify?.(err.message || 'Impossible de vérifier les versions en ligne.', 'danger')
    } finally {
      setChecking(false)
    }
  }

  const handleSavePolicy = async () => {
    if (!policy) return
    setSaving(true)
    try {
      const res = await api.saveUpdatesPolicy({
        debian: { selected_version: policy.debian?.selected_version || '' },
        kde: { selected_version: policy.kde?.selected_version || '' },
        lyux: { selected_version: policy.lyux?.selected_version || '' },
        auto_enforce: Boolean(policy.auto_enforce),
      })
      if (res?.policy) setPolicy(res.policy)
      notify?.('Versions cibles enregistrées pour les postes clients.', 'success')
    } catch (err) {
      notify?.(err.message || 'Erreur lors de la sauvegarde de la politique.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  const updateSelected = (key, value) => {
    setPolicy((prev) => ({
      ...prev,
      [key]: { ...(prev?.[key] || {}), selected_version: value },
    }))
  }

  return (
    <>
      <Card
        title="Versions cibles du parc (Debian / KDE / LyuX)"
        subtitle="Les postes clients s'arrêtent strictement à la version sélectionnée par le serveur"
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button icon="refresh" onClick={handleCheckLatest} disabled={checking || loading}>
              {checking ? 'Vérification...' : 'Vérifier dernières versions'}
            </Button>
            <Button variant="primary" icon="save" onClick={handleSavePolicy} disabled={saving || !policy}>
              {saving ? 'Enregistrement...' : 'Valider les cibles'}
            </Button>
          </div>
        }
      >
        {loading ? (
          <p className="muted">Chargement de la politique de versions...</p>
        ) : !policy ? (
          <p className="muted">En attente de connexion à l'API serveur.</p>
        ) : (
          <div className="stacked">
            {COMPONENT_KEYS.map(({ key, title, icon, hint }) => {
              const item = policy[key] || {}
              const latest = item.latest_version || ''
              const selected = item.selected_version || ''
              return (
                <SettingRow
                  key={key}
                  icon={icon}
                  title={title}
                  description={
                    <>
                      <span>{hint}</span>
                      {' · '}
                      <span>
                        Dernière existante :{' '}
                        <strong className="mono">{latest || 'Non vérifiée'}</strong>
                      </span>
                      {item.latest_error ? (
                        <span className="muted"> ({item.latest_error})</span>
                      ) : null}
                    </>
                  }
                  control={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <input
                        className="compact-input mono"
                        placeholder="Version cible serveur"
                        value={selected}
                        onChange={(e) => updateSelected(key, e.target.value)}
                      />
                      {latest && selected !== latest ? (
                        <Button size="sm" onClick={() => updateSelected(key, latest)}>
                          Aligner ({latest})
                        </Button>
                      ) : selected ? (
                        <Badge tone="success">Cible définie</Badge>
                      ) : (
                        <Badge tone="warning">Non définie</Badge>
                      )}
                    </div>
                  }
                />
              )
            })}
            <SettingRow
              icon="shield"
              title="Verrouillage APT sur les clients"
              description="Génère /etc/apt/preferences.d/lyux-policy.pref pour empêcher toute montée de version non validée."
              control={
                <Toggle
                  checked={Boolean(policy.auto_enforce)}
                  onChange={(val) => setPolicy((prev) => ({ ...prev, auto_enforce: val }))}
                  label="Verrouillage APT"
                />
              }
            />
          </div>
        )}
      </Card>

      <Card title="Politique de mise à jour" subtitle="Comportement du parc client">
        <SettingRow
          icon="download"
          title="Mises à jour automatiques"
          description="Diffuser automatiquement les nouvelles versions validées."
          control={<Toggle checked={form.autoUpdate} onChange={set('autoUpdate')} label="Mises à jour automatiques" />}
        />
        <SettingRow
          icon="clock"
          title="Fenêtre de déploiement"
          description="Plage horaire pendant laquelle les mises à jour sont appliquées."
          control={<input className="compact-input" value={form.updateWindow} onChange={(event) => set('updateWindow')(event.target.value)} />}
        />
        <SettingRow
          icon="database"
          title="Conservation des journaux"
          description="Nombre de jours pendant lesquels les journaux sont conservés."
          control={<input className="compact-input small" type="number" value={form.retention} onChange={(event) => set('retention')(Number(event.target.value))} />}
        />
      </Card>
      <ServerBuildCard />
    </>
  )
}
