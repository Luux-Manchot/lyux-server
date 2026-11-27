const TOKEN_KEY = 'lyux_admin_token'

export function getToken() {
  try {
    return window.localStorage.getItem(TOKEN_KEY) || ''
  } catch {
    return ''
  }
}

export function setToken(token) {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token)
    else window.localStorage.removeItem(TOKEN_KEY)
  } catch {
    // ignore storage errors
  }
}

export async function apiRequest(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(path, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    setToken('')
  }

  const text = await res.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (res.status === 401 && path !== '/api/v1/auth/login') {
    setToken('')
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('lyux:unauthorized'))
    }
  }
  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || `Erreur HTTP ${res.status}`
    throw new Error(message)
  }
  return data
}

export const api = {
  // Auth
  login: (username, password) =>
    apiRequest('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => apiRequest('/api/v1/auth/me'),
  logout: () => apiRequest('/api/v1/auth/logout', { method: 'POST' }),

  // Setup lycée
  getSetup: () => apiRequest('/api/v1/setup'),
  saveSetup: (payload) =>
    apiRequest('/api/v1/setup', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Dashboard & santé
  health: () => apiRequest('/api/v1/integrations/status'),
  systemMetrics: () => apiRequest('/api/v1/system/metrics'),
  dashboardSummary: () => apiRequest('/api/v1/dashboard/summary'),

  // Parc
  getBuildings: () => apiRequest('/api/v1/buildings'),
  createBuilding: (payload) =>
    apiRequest('/api/v1/buildings', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  deleteBuilding: (id) =>
    apiRequest(`/api/v1/buildings/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  getRooms: (buildingId) =>
    apiRequest(buildingId ? `/api/v1/rooms?building_id=${encodeURIComponent(buildingId)}` : '/api/v1/rooms'),
  createRoom: (payload) =>
    apiRequest('/api/v1/rooms', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  deleteRoom: (id) =>
    apiRequest(`/api/v1/rooms/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  getMachines: () => apiRequest('/api/v1/machines'),
  getInventory: () => apiRequest('/api/v1/parc/inventory'),
  wakeMachine: (hostname, mac) =>
    apiRequest('/api/v1/control/wake', {
      method: 'POST',
      body: JSON.stringify({ hostname, mac }),
    }),
  unlockAllMachines: () =>
    apiRequest('/api/v1/control/unlock-all', { method: 'POST' }),
  lockRoom: (roomId, action = 'lock', messageText = '') =>
    apiRequest('/api/v1/control/lock-room', {
      method: 'POST',
      body: JSON.stringify({ room_id: roomId, action, message_text: messageText }),
    }),

  // Logiciels
  getApps: () => apiRequest('/api/v1/apps'),
  searchAppStore: (query = '', source = 'all') =>
    apiRequest(`/api/v1/apps/store/search?q=${encodeURIComponent(query)}&source=${encodeURIComponent(source)}`),
  addApp: (payload) =>
    apiRequest('/api/v1/apps', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateApp: (appId, payload) =>
    apiRequest(`/api/v1/apps/${encodeURIComponent(appId)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteApp: (appId) =>
    apiRequest(`/api/v1/apps/${encodeURIComponent(appId)}`, { method: 'DELETE' }),
  deployApps: () => apiRequest('/api/v1/apps/deploy', { method: 'POST' }),

  // Utilisateurs & Classes
  getUsers: () => apiRequest('/api/v1/users'),
  createUser: (payload) =>
    apiRequest('/api/v1/users/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateUser: (username, payload) =>
    apiRequest(`/api/v1/users/${encodeURIComponent(username)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteUser: (username) =>
    apiRequest(`/api/v1/users/${encodeURIComponent(username)}`, { method: 'DELETE' }),
  resetPassword: (username, newPassword) =>
    apiRequest('/api/v1/control/reset-password', {
      method: 'POST',
      body: JSON.stringify({ username, new_password: newPassword }),
    }),
  getClasses: () => apiRequest('/api/v1/classes'),
  createClass: (payload) =>
    apiRequest('/api/v1/classes', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Rôles & Permissions
  getRoles: () => apiRequest('/api/v1/roles'),
  createRole: (payload) =>
    apiRequest('/api/v1/roles', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  deleteRole: (roleId) =>
    apiRequest(`/api/v1/roles/${encodeURIComponent(roleId)}`, { method: 'DELETE' }),
  updatePermissions: (matrix) =>
    apiRequest('/api/v1/roles/permissions', {
      method: 'PUT',
      body: JSON.stringify({ matrix }),
    }),

  // Profils globaux (lycée)
  getProfiles: () => apiRequest('/api/v1/profiles'),
  saveProfile: (payload) =>
    apiRequest('/api/v1/profiles', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  previewProfile: (payload) =>
    apiRequest('/api/v1/profiles/preview', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  pilotProfile: (payload) =>
    apiRequest('/api/v1/profiles/pilot', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  resetProfile: (profileId) =>
    apiRequest(`/api/v1/profiles/${encodeURIComponent(profileId)}/reset`, { method: 'POST' }),
  assignProfile: (payload) =>
    apiRequest('/api/v1/profiles/assign', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  unassignProfile: (payload) =>
    apiRequest('/api/v1/profiles/unassign', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  deleteProfile: (profileId) =>
    apiRequest(`/api/v1/profiles/${encodeURIComponent(profileId)}`, { method: 'DELETE' }),

  // Releases & Mises à jour
  getReleases: () => apiRequest('/api/v1/releases'),
  createRelease: (payload) =>
    apiRequest('/api/v1/releases', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  signRelease: (id) =>
    apiRequest(`/api/v1/releases/${encodeURIComponent(id)}/sign`, { method: 'POST' }),
  publishRelease: (id) =>
    apiRequest(`/api/v1/releases/${encodeURIComponent(id)}/publish`, { method: 'POST' }),
  revokeRelease: (id, reason = '') =>
    apiRequest(`/api/v1/releases/${encodeURIComponent(id)}/revoke`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  rollbackRelease: (id) =>
    apiRequest(`/api/v1/releases/${encodeURIComponent(id)}/rollback`, { method: 'POST' }),
  rotateReleaseKeys: () =>
    apiRequest('/api/v1/releases/keys/rotate', { method: 'POST' }),
  getReleaseAudit: () => apiRequest('/api/v1/releases/audit'),
  updateReleasePolicy: (policy) =>
    apiRequest('/api/v1/releases/policy', {
      method: 'PUT',
      body: JSON.stringify(policy),
    }),
  checkUpdates: () => apiRequest('/api/v1/system/updates/check'),
  applyUpdates: () => apiRequest('/api/v1/system/updates/apply', { method: 'POST' }),
  getUpdatesPolicy: () => apiRequest('/api/v1/updates/policy'),
  saveUpdatesPolicy: (payload) =>
    apiRequest('/api/v1/updates/policy', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  checkUpdatesPolicyLatest: () =>
    apiRequest('/api/v1/updates/policy/check', { method: 'POST' }),

  // Réglages
  getSettings: () => apiRequest('/api/v1/system/settings'),
  saveSettings: (payload) =>
    apiRequest('/api/v1/system/settings', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
}
