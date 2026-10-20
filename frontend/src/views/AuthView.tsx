import React, { useState } from 'react'
import { api, setToken } from '../api'

export default function AuthView({ onAuthed }: { onAuthed: (u: any) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const data = await api(`/auth/${mode}`, { method: 'POST', body: { email, password } })
      setToken(data.access_token)
      onAuthed(await api('/auth/me'))
    } catch (err: any) { setError(err.message) } finally { setBusy(false) }
  }

  return (
    <div className="h-full flex items-center justify-center">
      <form onSubmit={submit} className="w-80 bg-ink-900 border border-ink-700 rounded-xl p-6 space-y-4">
        <div className="text-lg font-semibold text-accent-bright">Foe Agent</div>
        <div className="text-sm text-slate-400">{mode === 'login' ? 'Sign in' : 'Create an account'}</div>
        <input className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="password (min 8 chars)" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <div className="text-sm text-red-400">{error}</div>}
        <button disabled={busy} className="w-full bg-accent hover:bg-accent/90 disabled:opacity-50 text-white rounded-md py-2 text-sm font-medium">
          {busy ? 'Working...' : mode === 'login' ? 'Sign in' : 'Register'}
        </button>
        <button type="button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
          className="text-xs text-slate-400 hover:text-white">
          {mode === 'login' ? 'No account yet? Register' : 'Already registered? Sign in'}
        </button>
      </form>
    </div>
  )
}
