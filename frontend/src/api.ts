import axios from 'axios'

// VITE_API_URL is empty for local dev (the Vite dev server proxies /api and /ws
// to the backend — see vite.config.ts), and set to the API's public host on
// Render. Accept a bare hostname (what Render's fromService exposes) or a full
// URL, and normalise to an https origin.
const raw = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
const apiBase = raw ? (/^https?:\/\//.test(raw) ? raw : `https://${raw}`) : ''

export const api = axios.create({ baseURL: `${apiBase}/api/v1` })

// Build the WebSocket URL. With an explicit API origin, reuse it (http->ws,
// https->wss). Otherwise fall back to same-origin so the dev proxy handles it.
export function wsUrl(path = '/ws/metrics'): string {
  if (apiBase) return apiBase.replace(/^http/, 'ws') + path
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}${path}`
}
