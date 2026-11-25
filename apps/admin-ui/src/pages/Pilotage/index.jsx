import React, { useEffect, useMemo, useState } from 'react'
import { Button, PageActions } from '../../components.jsx'
import { api } from '../../api/client.js'
import './Pilotage.css'
import ServerCard from './components/ServerCard.jsx'
import ClientFleetCard from './components/ClientFleetCard.jsx'
import VersionDistribution from './components/VersionDistribution.jsx'
import FleetTable from './components/FleetTable.jsx'
import DeploymentHistory from './components/DeploymentHistory.jsx'

export default function Pilotage({ notify, navigate }) {
  const [machines, setMachines] = useState([])
  const [serverSettings, setServerSettings] = useState(null)
  const [search, setSearch] = useState('')
  const [autoUpdate, setAutoUpdate] = useState(true)

  useEffect(() => {
    api.getInventory()
      .then((res) => {
        if (Array.isArray(res?.machines)) {
          setMachines(res.machines.map((m) => ({
            ...m,
            updates: m.is_up_to_date ? 0 : 1,
            session: m.session || 'Aucune',
          })))
        }
      })
      .catch(() => {})
    api.getSettings()
      .then((res) => {
        if (res) {
          setServerSettings(res)
          if (typeof res.auto_update_clients === 'boolean') {
            setAutoUpdate(res.auto_update_clients)
          }
        }
      })
      .catch(() => {})
  }, [])

  const upToDate = machines.filter((machine) => machine.updates === 0).length
  const syncRate = machines.length ? Math.round((upToDate / machines.length) * 100) : 100

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return machines.filter((machine) => !term || machine.hostname.toLowerCase().includes(term) || machine.ip.includes(term))
  }, [machines, search])

  const handleToggleAutoUpdate = async (nextValue) => {
    const prev = autoUpdate
    setAutoUpdate(nextValue)
    try {
      await api.saveSettings({ auto_update_clients: nextValue })
      notify(nextValue ? 'Mises à jour automatiques activées.' : 'Mises à jour automatiques désactivées.', nextValue ? 'success' : 'warning')
    } catch (err) {
      setAutoUpdate(prev)
      notify(err.message || 'Erreur lors de la mise à jour du paramètre.', 'danger')
    }
  }

  const handleCheckUpdates = async () => {
    try {
      const res = await api.checkUpdates()
      notify(res.message || 'Vérification effectuée.', 'info')
    } catch (err) {
      notify(err.message || 'Impossible de vérifier les mises à jour.', 'danger')
    }
  }

  return (
    <>
      <PageActions>
        <Button icon="package" onClick={() => navigate('paquets')}>
          Versions OS & Dépôt
        </Button>
        <Button variant="primary" icon="refresh" onClick={handleCheckUpdates}>
          Vérifier les mises à jour
        </Button>
      </PageActions>

      <div className="grid-1-1">
        <ServerCard notify={notify} serverSettings={serverSettings} />
        <ClientFleetCard
          notify={notify}
          autoUpdate={autoUpdate}
          syncRate={syncRate}
          upToDate={upToDate}
          totalMachines={machines.length}
          targetVersion={serverSettings?.lyux_version || '1.0.0'}
          aptCache={serverSettings?.apt_cache_enabled ?? true}
        />
      </div>

      <VersionDistribution machines={machines} targetVersion={serverSettings?.lyux_version || '1.0.0'} />

      <FleetTable
        notify={notify}
        search={search}
        onSearch={setSearch}
        autoUpdate={autoUpdate}
        onAutoUpdateChange={handleToggleAutoUpdate}
        rows={filtered}
      />

      <DeploymentHistory />
    </>
  )
}
