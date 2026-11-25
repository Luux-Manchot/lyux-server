import React, { useEffect, useState } from 'react'
import { Badge, Button, Card, PageActions, SettingRow, Toggle } from '../../components.jsx'
import { Icon } from '../../icons.jsx'
import { api } from '../../api/client.js'
import './Setup.css'

const STEPS = [
  { id: 'identity', num: 1, title: 'Établissement', subtitle: 'Nom, UAI, domaine' },
  { id: 'network', num: 2, title: 'Réseau & Services', subtitle: 'IP, AD, GLPI, cache' },
  { id: 'topology', num: 3, title: 'Bâtiments & Salles', subtitle: 'Structure du parc' },
  { id: 'policy', num: 4, title: 'Politique & Validation', subtitle: 'Enrôlement & application' },
]

const PROFILE_OPTIONS = [
  { value: 'standard', label: 'Standard (Bureautique)' },
  { value: 'nsi', label: 'NSI / Informatique' },
  { value: 'sciences', label: 'Sciences (Physique / SVT)' },
  { value: 'multimedia', label: 'Multimédia / CDI' },
  { value: 'atelier', label: 'Ateliers technologiques' },
]

export default function Setup({ notify, onSetupSaved }) {
  const [step, setStep] = useState('identity')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [form, setForm] = useState({
    configured: false,
    school_name: 'Lycée Opération Manchot',
    uai_code: '',
    academy: '',
    school_year: '2026 – 2027',
    domain: 'lyux.lan',
    admin_email: 'administration@lyux.lan',
    timezone: 'Europe/Paris',
    network: {
      server_ip: '192.168.10.1',
      subnet: '192.168.10.0/24',
      gateway: '192.168.10.254',
      dns: '192.168.10.1',
    },
    modules: {
      samba_ad: true,
      glpi: true,
      uptime_kuma: true,
      apt_cache: true,
      veyon: true,
      sso: false,
    },
    enrollment_enabled: true,
    auto_update: true,
    update_window: '22:00 – 05:00',
  })

  const [buildings, setBuildings] = useState([
    { id: 'BAT-A', name: 'Bâtiment A', description: 'Administration et accueil' },
    { id: 'BAT-B', name: 'Bâtiment B', description: 'Enseignement général' },
    { id: 'BAT-C', name: 'Bâtiment C', description: 'Pôle Sciences et NSI' },
  ])
  const [rooms, setRooms] = useState([
    { id: 'C14', building_id: 'BAT-C', profile: 'nsi', capacity: 24, teacher: '' },
    { id: 'B204', building_id: 'BAT-B', profile: 'standard', capacity: 24, teacher: '' },
    { id: 'S102', building_id: 'BAT-C', profile: 'sciences', capacity: 24, teacher: '' },
  ])
  const [applyTopology, setApplyTopology] = useState(false)

  const [newBldName, setNewBldName] = useState('')
  const [newRoomId, setNewRoomId] = useState('')
  const [newRoomBld, setNewRoomBld] = useState('BAT-C')
  const [newRoomProfile, setNewRoomProfile] = useState('standard')
  const [newRoomCapacity, setNewRoomCapacity] = useState(24)

  useEffect(() => {
    let active = true
    Promise.all([
      api.getSetup().catch(() => null),
      api.getBuildings().catch(() => null),
      api.getRooms().catch(() => null),
    ]).then(([setupRes, bldRes, roomRes]) => {
      if (!active) return
      if (setupRes) {
        setForm((prev) => ({
          ...prev,
          ...setupRes,
          network: { ...prev.network, ...(setupRes.network || {}) },
          modules: { ...prev.modules, ...(setupRes.modules || {}) },
        }))
      }
      if (Array.isArray(bldRes) && bldRes.length > 0) {
        setBuildings(bldRes)
        setNewRoomBld(bldRes[0].id)
      }
      if (Array.isArray(roomRes) && roomRes.length > 0) {
        setRooms(roomRes.map((r) => ({
          id: r.id,
          building_id: r.building_id || r.buildingId || 'BAT-C',
          profile: r.profile || 'standard',
          capacity: r.capacity || 24,
          teacher: r.teacher || '',
        })))
      }
      setLoading(false)
    })
    return () => { active = false }
  }, [])

  const updateField = (key, value) => setForm((prev) => ({ ...prev, [key]: value }))
  const updateNetwork = (key, value) => setForm((prev) => ({ ...prev, network: { ...prev.network, [key]: value } }))
  const toggleModule = (key) => setForm((prev) => ({ ...prev, modules: { ...prev.modules, [key]: !prev.modules[key] } }))

  const addBuilding = () => {
    const name = newBldName.trim()
    if (!name) return
    const id = `BAT-${name.replace(/[^A-Za-z0-9]/g, '').slice(0, 4).toUpperCase() || buildings.length + 1}`
    if (buildings.some((b) => b.id === id)) {
      notify(`Le bâtiment ${id} existe déjà.`, 'warning')
      return
    }
    setBuildings((prev) => [...prev, { id, name, description: 'Ajouté depuis la configuration lycée' }])
    setNewBldName('')
  }

  const addRoom = () => {
    const id = newRoomId.trim().toUpperCase()
    if (!id) return
    if (rooms.some((r) => r.id === id)) {
      notify(`La salle ${id} existe déjà.`, 'warning')
      return
    }
    setRooms((prev) => [
      ...prev,
      { id, building_id: newRoomBld, profile: newRoomProfile, capacity: Number(newRoomCapacity) || 24, teacher: '' },
    ])
    setNewRoomId('')
  }

  const handleSave = async () => {
    if (!form.school_name.trim()) {
      notify('Le nom de l’établissement est obligatoire.', 'warning')
      return
    }
    setSaving(true)
    try {
      const res = await api.saveSetup({
        ...form,
        buildings,
        rooms,
        apply_topology: applyTopology,
      })
      setForm((prev) => ({ ...prev, configured: true, updated_at: res.setup?.updated_at }))
      notify(
        applyTopology
          ? `Configuration enregistrée (${res.created_buildings} bâtiments, ${res.created_rooms} salles appliqués).`
          : 'Configuration de l’établissement enregistrée.',
        'success',
      )
      if (onSetupSaved) onSetupSaved(res.setup)
    } catch (err) {
      notify(err.message || 'Erreur lors de la sauvegarde.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Card title="Configuration de l’établissement">
        <p className="muted">Chargement de la configuration serveur…</p>
      </Card>
    )
  }

  return (
    <>
      <PageActions>
        <Badge tone={form.configured ? 'success' : 'warning'} dot>
          {form.configured ? 'Établissement configuré' : 'Configuration initiale requise'}
        </Badge>
        <Button variant="primary" icon="save" disabled={saving} onClick={handleSave}>
          {saving ? 'Enregistrement…' : 'Enregistrer la configuration'}
        </Button>
      </PageActions>

      <div className="setup-steps">
        {STEPS.map((s) => (
          <button
            type="button"
            key={s.id}
            className={`setup-step ${step === s.id ? 'active' : ''}`}
            onClick={() => setStep(s.id)}
          >
            <span className="setup-step-num">{s.num}</span>
            <span className="setup-step-text">
              <strong>{s.title}</strong>
              <small>{s.subtitle}</small>
            </span>
          </button>
        ))}
      </div>

      {step === 'identity' && (
        <Card title="Identité de l’établissement" subtitle="Informations générales utilisées sur le domaine, les certificats et les postes clients">
          <div className="form-grid">
            <label className="form-field">
              <span className="form-label">Nom du lycée / établissement</span>
              <input value={form.school_name} onChange={(e) => updateField('school_name', e.target.value)} />
            </label>
            <label className="form-field">
              <span className="form-label">Code UAI (RNE)</span>
              <input value={form.uai_code} onChange={(e) => updateField('uai_code', e.target.value)} placeholder="ex. 0751234A" />
            </label>
            <label className="form-field">
              <span className="form-label">Académie</span>
              <input value={form.academy} onChange={(e) => updateField('academy', e.target.value)} placeholder="ex. Académie de Lyon" />
            </label>
            <label className="form-field">
              <span className="form-label">Année scolaire</span>
              <input value={form.school_year} onChange={(e) => updateField('school_year', e.target.value)} />
            </label>
            <label className="form-field">
              <span className="form-label">Domaine local Active Directory</span>
              <input value={form.domain} onChange={(e) => updateField('domain', e.target.value)} />
            </label>
            <label className="form-field">
              <span className="form-label">Courriel de contact technique</span>
              <input type="email" value={form.admin_email} onChange={(e) => updateField('admin_email', e.target.value)} />
            </label>
          </div>
          <div className="setup-footer-bar">
            <span className="muted">Étape 1 sur 4</span>
            <Button variant="primary" icon="chevronRight" onClick={() => setStep('network')}>
              Suivant : Réseau & Services
            </Button>
          </div>
        </Card>
      )}

      {step === 'network' && (
        <div className="grid-1-1">
          <Card title="Paramètres réseau du serveur" subtitle="Adressage utilisé par le serveur LyuX et le fichier preseed">
            <div className="form-stack">
              <label className="form-field">
                <span className="form-label">Adresse IP du serveur LyuX</span>
                <input value={form.network.server_ip} onChange={(e) => updateNetwork('server_ip', e.target.value)} />
              </label>
              <label className="form-field">
                <span className="form-label">Sous-réseau pédagogique</span>
                <input value={form.network.subnet} onChange={(e) => updateNetwork('subnet', e.target.value)} />
              </label>
              <label className="form-field">
                <span className="form-label">Passerelle par défaut</span>
                <input value={form.network.gateway} onChange={(e) => updateNetwork('gateway', e.target.value)} />
              </label>
              <label className="form-field">
                <span className="form-label">Serveur DNS principal</span>
                <input value={form.network.dns} onChange={(e) => updateNetwork('dns', e.target.value)} />
              </label>
            </div>
          </Card>

          <Card title="Services activés" subtitle="Briquettes Docker et outils pédagogiques à activer pour ce lycée">
            <SettingRow
              icon="users"
              title="Samba 4 Active Directory"
              description="Annuaire centralisé, sessions élèves/profs et partages CIFS."
              control={<Toggle checked={!!form.modules.samba_ad} onChange={() => toggleModule('samba_ad')} label="Samba AD" />}
            />
            <SettingRow
              icon="layers"
              title="GLPI (Inventaire & Tickets)"
              description="Remontée automatique du matériel et support incidents."
              control={<Toggle checked={!!form.modules.glpi} onChange={() => toggleModule('glpi')} label="GLPI" />}
            />
            <SettingRow
              icon="activity"
              title="Uptime Kuma"
              description="Supervision des services et alertes de disponibilité."
              control={<Toggle checked={!!form.modules.uptime_kuma} onChange={() => toggleModule('uptime_kuma')} label="Uptime Kuma" />}
            />
            <SettingRow
              icon="download"
              title="Cache APT local (port 3142)"
              description="Accélère l’installation et les mises à jour des postes."
              control={<Toggle checked={!!form.modules.apt_cache} onChange={() => toggleModule('apt_cache')} label="Cache APT" />}
            />
            <SettingRow
              icon="monitor"
              title="Veyon (Contrôle de classe)"
              description="Verrouillage d’écran et supervision par les enseignants."
              control={<Toggle checked={!!form.modules.veyon} onChange={() => toggleModule('veyon')} label="Veyon" />}
            />
            <div className="setup-footer-bar">
              <Button onClick={() => setStep('identity')}>Précédent</Button>
              <Button variant="primary" icon="chevronRight" onClick={() => setStep('topology')}>
                Suivant : Bâtiments & Salles
              </Button>
            </div>
          </Card>
        </div>
      )}

      {step === 'topology' && (
        <Card title="Structure du parc informatique" subtitle="Définissez les bâtiments et les salles types de votre établissement">
          <div className="setup-topology-grid">
            <div>
              <p className="subheading">Bâtiments ({buildings.length})</p>
              {buildings.map((b) => (
                <div className="setup-list-row" key={b.id}>
                  <div>
                    <strong>{b.name}</strong> <span className="mono muted">({b.id})</span>
                    <div><small>{b.description || '—'}</small></div>
                  </div>
                  <Button
                    size="sm"
                    icon="trash"
                    onClick={() => setBuildings((prev) => prev.filter((item) => item.id !== b.id))}
                  />
                </div>
              ))}
              <div className="setup-inline-add">
                <input
                  value={newBldName}
                  onChange={(e) => setNewBldName(e.target.value)}
                  placeholder="Nom (ex. Bâtiment H)"
                />
                <Button size="sm" icon="plus" onClick={addBuilding}>Ajouter bâtiment</Button>
              </div>
            </div>

            <div>
              <p className="subheading">Salles ({rooms.length})</p>
              {rooms.map((r) => (
                <div className="setup-list-row" key={r.id}>
                  <div>
                    <strong>Salle {r.id}</strong> <span className="muted">· {r.building_id}</span>
                    <div><small>Profil : {r.profile} · {r.capacity} postes</small></div>
                  </div>
                  <Button
                    size="sm"
                    icon="trash"
                    onClick={() => setRooms((prev) => prev.filter((item) => item.id !== r.id))}
                  />
                </div>
              ))}
              <div className="setup-inline-add">
                <input
                  style={{ width: 90 }}
                  value={newRoomId}
                  onChange={(e) => setNewRoomId(e.target.value)}
                  placeholder="Salle (C15)"
                />
                <select value={newRoomBld} onChange={(e) => setNewRoomBld(e.target.value)}>
                  {buildings.map((b) => <option key={b.id} value={b.id}>{b.id}</option>)}
                </select>
                <select value={newRoomProfile} onChange={(e) => setNewRoomProfile(e.target.value)}>
                  {PROFILE_OPTIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
                <input
                  style={{ width: 65 }}
                  type="number"
                  min={1}
                  max={60}
                  value={newRoomCapacity}
                  onChange={(e) => setNewRoomCapacity(e.target.value)}
                />
                <Button size="sm" icon="plus" onClick={addRoom}>Ajouter salle</Button>
              </div>
            </div>
          </div>

          <div className="note-box">
            <Icon name="info" size={16} />
            <p>
              Cochez « Appliquer cette topologie au parc » à l’étape suivante si vous souhaitez remplacer/injecter ces bâtiments et salles dans l’inventaire actif du serveur.
            </p>
          </div>

          <div className="setup-footer-bar">
            <Button onClick={() => setStep('network')}>Précédent</Button>
            <Button variant="primary" icon="chevronRight" onClick={() => setStep('policy')}>
              Suivant : Politique & Validation
            </Button>
          </div>
        </Card>
      )}

      {step === 'policy' && (
        <Card title="Politique de déploiement & Validation" subtitle="Derniers réglages avant d’enregistrer l’installation de l’établissement">
          <SettingRow
            icon="lock"
            title="Enrôlement OOBE des nouveaux postes"
            description="Autoriser les nouveaux PC à s’enrôler automatiquement dans le domaine."
            control={
              <Toggle
                checked={form.enrollment_enabled}
                onChange={() => updateField('enrollment_enabled', !form.enrollment_enabled)}
                label="Enrôlement OOBE"
              />
            }
          />
          <SettingRow
            icon="refresh"
            title="Mises à jour automatiques du parc"
            description="Appliquer les mises à jour système et logicielles durant la fenêtre nocturne."
            control={
              <Toggle
                checked={form.auto_update}
                onChange={() => updateField('auto_update', !form.auto_update)}
                label="Mises à jour auto"
              />
            }
          />
          <SettingRow
            icon="clock"
            title="Fenêtre horaire de maintenance"
            description="Plage de déploiement silencieux."
            control={
              <input
                className="compact-input"
                value={form.update_window}
                onChange={(e) => updateField('update_window', e.target.value)}
              />
            }
          />
          <SettingRow
            icon="building"
            title="Appliquer cette topologie au parc actif"
            description="Injecte les bâtiments et salles définis à l’étape 3 dans l’API serveur."
            control={
              <Toggle
                checked={applyTopology}
                onChange={() => setApplyTopology((v) => !v)}
                label="Appliquer topologie"
              />
            }
          />

          <div className="setup-footer-bar">
            <Button onClick={() => setStep('topology')}>Précédent</Button>
            <Button variant="primary" icon="check" disabled={saving} onClick={handleSave}>
              {saving ? 'Application en cours…' : 'Valider et enregistrer la configuration'}
            </Button>
          </div>
        </Card>
      )}
    </>
  )
}
