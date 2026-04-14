const API_BASE = '/api'

// Helper function for API calls
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }))
    throw new Error(error.message || `API Error: ${response.status}`)
  }

  return response.json()
}

// Digest endpoints
export const digests = {
  list: () => apiCall('/digests/'),
  create: (data) => apiCall('/digests/', { method: 'POST', body: JSON.stringify(data) }),
  get: (id) => apiCall(`/digests/${id}`),
  update: (id, data) => apiCall(`/digests/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => apiCall(`/digests/${id}`, { method: 'DELETE' }),
  run: (id) => apiCall(`/digests/${id}/run`, { method: 'POST' }),
}

// Filter endpoints
export const filters = {
  list: (digestId) => apiCall(`/digests/${digestId}/filters/`),
  create: (digestId, data) =>
    apiCall(`/digests/${digestId}/filters/`, { method: 'POST', body: JSON.stringify(data) }),
  delete: (digestId, filterId) => apiCall(`/digests/${digestId}/filters/${filterId}`, { method: 'DELETE' }),
}

// Channel endpoints
export const channels = {
  list: (digestId) => apiCall(`/digests/${digestId}/channels/`),
  create: (digestId, data) =>
    apiCall(`/digests/${digestId}/channels/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (digestId, channelId, data) =>
    apiCall(`/digests/${digestId}/channels/${channelId}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (digestId, channelId) =>
    apiCall(`/digests/${digestId}/channels/${channelId}`, { method: 'DELETE' }),
}

// History endpoints
export const history = {
  list: (digestId) => apiCall(`/digests/${digestId}/history/`),
}

// Gmail endpoints
export const gmail = {
  getAuthUrl: () => apiCall('/auth/gmail/url'),
  callback: (code) => apiCall(`/auth/gmail/callback?code=${code}`),
  status: () => apiCall('/auth/gmail/status'),
}

// Scheduler endpoints
export const scheduler = {
  status: () => apiCall('/scheduler/status'),
  start: () => apiCall('/scheduler/start', { method: 'POST' }),
  stop: () => apiCall('/scheduler/stop', { method: 'POST' }),
}
