import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function ProjectsView({ projectId, setProjectId }: any) {
  const [projects, setProjects] = useState<any[]>([])
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  async function refresh() { setProjects(await api('/projects').catch(() => [])) }
  useEffect(() => { refresh() }, [])

  async function create() {
    if (!name.trim()) return
    setError('')
    try {
      const p = await api('/projects', { method: 'POST', body: { name, description: '' } })
      setName(''); setProjectId(p.id); refresh()
    } catch (e: any) { setError(e.message) }
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-3xl w-full mx-auto space-y-4">
      <div className="flex gap-2">
        <input className="flex-1 bg-ink-900 border border-ink-600 rounded-md px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="New project name" value={name} onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && create()} />
        <button onClick={create} className="bg-accent hover:bg-accent/90 text-white rounded-md px-4 text-sm">Create</button>
      </div>
      {error && <div className="text-sm text-red-400">{error}</div>}
      {projects.map((p) => (
        <button key={p.id} onClick={() => setProjectId(p.id)}
          className={`block w-full text-left bg-ink-900 border rounded-lg px-4 py-3 ${projectId === p.id ? 'border-accent' : 'border-ink-700'} hover:border-accent/60`}>
          <div className="font-medium text-sm">{p.name}</div>
          <div className="text-xs text-slate-500">{p.description || 'no description'}</div>
        </button>
      ))}
      {projects.length === 0 && <div className="text-sm text-slate-500">No projects yet. Create one: agent runs get their own isolated workspace folder.</div>}
    </div>
  )
}
