import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function SettingsView({ providerId, setProviderId }: any) {
  const [providers, setProviders] = useState<any[]>([])
  const [form, setForm] = useState({ name: '', kind: 'ollama', base_url: 'http://localhost:11434', model: '', api_key: '', is_default: false })
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')

  async function refresh() { setProviders(await api('/models').catch(() => [])) }
  useEffect(() => { refresh() }, [])

  async function save() {
    setError(''); setMsg('')
    try {
      const p = await api('/models', { method: 'POST', body: form })
      const result = await api(`/models/${p.id}/test`, { method: 'POST' })
      if (result.ok) { setMsg(`Connected to ${form.base_url}. Models: ${(result.models || []).slice(0, 8).join(', ')}`); setProviderId(p.id) }
      else setError(result.error)
      setForm({ ...form, name: '', api_key: '' }); refresh()
    } catch (e: any) { setError(e.message) }
  }

  async function test(id: number) {
    setError(''); setMsg('')
    const result = await api(`/models/${id}/test`, { method: 'POST' }).catch((e: any) => ({ ok: false, error: e.message }))
    if (result.ok) { setMsg(`Connected. Models: ${(result.models || []).slice(0, 8).join(', ')}`); setProviderId(id) }
    else setError(result.error)
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-3xl w-full mx-auto space-y-4 text-sm">
      <div className="bg-ink-900 border border-ink-700 rounded-lg p-4 space-y-3">
        <div className="font-medium">Add a model provider</div>
        <div className="grid grid-cols-2 gap-2">
          <input className="bg-ink-950 border border-ink-600 rounded-md px-3 py-2 outline-none focus:border-accent" placeholder="Name (e.g. local ollama)"
            value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <select className="bg-ink-950 border border-ink-600 rounded-md px-3 py-2 outline-none"
            value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            <option value="ollama">Ollama</option>
            <option value="openai_compat">OpenAI-compatible (llama.cpp, Groq, LM Studio...)</option>
          </select>
          <input className="bg-ink-950 border border-ink-600 rounded-md px-3 py-2 outline-none focus:border-accent" placeholder="Base URL"
            value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
          <input className="bg-ink-950 border border-ink-600 rounded-md px-3 py-2 outline-none focus:border-accent" placeholder="Model (e.g. llama3.2:1b)"
            value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
          <input className="bg-ink-950 border border-ink-600 rounded-md px-3 py-2 outline-none focus:border-accent" placeholder="API key (optional, stored server-side only)"
            value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
          <label className="flex items-center gap-2 text-slate-400"><input type="checkbox" checked={form.is_default}
            onChange={(e) => setForm({ ...form, is_default: e.target.checked })} /> default</label>
        </div>
        <button onClick={save} className="bg-accent hover:bg-accent/90 text-white rounded-md px-4 py-2">Save and test connection</button>
        {msg && <div className="text-emerald-400">{msg}</div>}
        {error && <div className="text-red-400">{error}</div>}
      </div>
      {providers.map((p) => (
        <div key={p.id} className="bg-ink-900 border border-ink-700 rounded-lg px-4 py-3 flex items-center justify-between">
          <div>
            <div className="font-medium">{p.name} {providerId === p.id && <span className="text-xs text-accent-bright">- active</span>}</div>
            <div className="text-xs text-slate-500">{p.kind} | {p.base_url} | {p.model} {p.has_key ? '| key saved' : ''}</div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => test(p.id)} className="border border-ink-600 hover:border-accent rounded-md px-3 py-1 text-xs">Test</button>
            <button onClick={async () => { await api(`/models/${p.id}`, { method: 'DELETE' }).catch(() => {}); refresh() }}
              className="text-xs text-red-400 hover:text-red-300">Delete</button>
          </div>
        </div>
      ))}
    </div>
  )
}
