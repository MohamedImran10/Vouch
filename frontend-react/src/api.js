const API_ROOT = import.meta.env.VITE_API_URL || 'http://localhost:8001'
const TOKEN_KEY = 'vouch.accessToken'

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function saveAccessToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')
  if (options.body) headers.set('Content-Type', 'application/json')
  const token = getAccessToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers })
  const body = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    const detail = body?.detail || body?.message || `Request failed (${response.status})`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return body
}

export const api = {
  health: () => request('/health'),
  login: (email, password) => request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  }),
  categories: async () => (await request('/api/categories')).categories,
  providers: (category) => {
    const query = new URLSearchParams({ limit: '100' })
    if (category) query.set('category', category)
    return request(`/api/providers?${query}`)
  },
  vouches: (userId, category) => {
    const query = new URLSearchParams({ user_id: userId, limit: '100' })
    if (category && category !== 'all') query.set('category', category)
      return request(`/api/vouches?${query}`).then((vouches) =>
        vouches.filter((vouch) => vouch.category !== 'friend'),
      )
  },
  createProvider: (provider) => request('/api/providers', {
    method: 'POST',
    body: JSON.stringify(provider),
  }),
  deleteProvider: (id) => request(`/api/providers/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  }),
  createVouch: (vouch) => request('/api/vouches', {
    method: 'POST',
    body: JSON.stringify(vouch),
  }),
  updateVouch: (id, vouch) => request(`/api/vouches/${encodeURIComponent(id)}`, {
    method: 'PUT',
    body: JSON.stringify(vouch),
  }),
  deleteVouch: (id) => request(`/api/vouches/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  }),
  graph: () => request('/api/graph/full'),
}
