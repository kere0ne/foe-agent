const BASE = '/api'

export function getToken() { return localStorage.getItem('foe_token') || '' }
export function setToken(t: string) { localStorage.setItem('foe_token', t) }
export function clearToken() { localStorage.removeItem('foe_token') }

export async function api(path: string, opts: any = {}) {
  const res = await fetch(BASE + path, {
    method: opts.method || 'GET',
    headers: { Authorization: `Bearer ${getToken()}`, ...(opts.body ? { 'Content-Type': 'application/json' } : {}), ...(opts.headers || {}) },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  })
  if (res.status === 401) { clearToken(); window.location.reload(); throw new Error('Session expired') }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function putFile(projectId: number, path: string, content: string) {
  const res = await fetch(`${BASE}/projects/${projectId}/files?path=${encodeURIComponent(path)}`, {
    method: 'PUT', headers: { Authorization: `Bearer ${getToken()}` }, body: content,
  })
  if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || 'write failed') }
  return res.json()
}

export async function streamChat(conversationId: number, content: string, providerId: number,
  onChunk: (t: string) => void, onError: (e: string) => void, onDone: () => void) {
  const res = await fetch(`${BASE}/conversations/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify({ conversation_id: conversationId, content, provider_id: providerId }),
  })
  if (!res.ok || !res.body) { onError('Chat request failed: HTTP ' + res.status); onDone(); return }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''
    for (const evt of events) {
      const line = evt.replace(/^data: /, '')
      if (!line.trim()) continue
      try {
        const data = JSON.parse(line)
        if (data.chunk) onChunk(data.chunk)
        if (data.error) onError(data.error)
        if (data.done) onDone()
      } catch { /* ignore malformed frame */ }
    }
  }
  onDone()
}
