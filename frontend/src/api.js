const BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'
export const session = {
  get: () => JSON.parse(localStorage.getItem('cm_session') || 'null'),
  set: (s) => localStorage.setItem('cm_session', JSON.stringify(s)),
  clear: () => localStorage.removeItem('cm_session'),
}
export async function api(path, { method = 'GET', body, form } = {}) {
  const headers = {}; const s = session.get()
  if (s) headers.Authorization = `Bearer ${s.token}`
  if (body) headers['Content-Type'] = 'application/json'
  const res = await fetch(BASE + path, { method, headers, body: form || (body && JSON.stringify(body)) })
  const data = await res.json().catch(() => ({}))
  if (import.meta.env.DEV) console.debug('[api]', method, path, res.status, data)
  if (res.status === 401 && s) { session.clear(); window.location.assign('/login') }
  if (!res.ok) throw new Error(data.error || 'Something went wrong')
  return data
}
