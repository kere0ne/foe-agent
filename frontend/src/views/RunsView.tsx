import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api'

export default function RunsView({ projectId, setProjectId, providerId }: any) {
  const [runs, setRuns] = useState<any[]>([])
  const [goal, setGoal] = useState('')
  const [detail, setDetail] = useState<any>(null)
  const [error, setError] = useState('')
  const poll = useRef<any>(null)

  async function refresh() {
    if (!projectId) { setRuns([]); return }
    setRuns(await api(`/projects/${projectId}/runs`).catch(() => []))
  }
  useEffect(() => { refresh(); return () => clearInterval(poll.current) }, [projectId])

  async function start() {
    if (!projectId) { setError('Create a project first (Projects tab)'); return }
    if (!providerId) { setError('Add a model in Settings first'); return }
    if (!goal.trim()) return
    setError('')
    try {
      const r = await api(`/projects/${projectId}/runs`, { method: 'POST', body: { goal, provider_id: providerId } })
      setGoal(''); setDetail(r); watch(r.id)
    } catch (e: any) { setError(e.message) }
  }

  function watch(id: number) {
    clearInterval(poll.current)
    poll.current = setInterval(async () => {
      const d = await api(`/projects/${projectId}/runs/${id}`).catch(() => null)
      if (d) setDetail(d)
      if (d && ['complete', 'failed', 'cancelled'].includes(d.state)) clearInterval(poll.current)
    }, 2000)
  }

  async function cancel() {
    if (!detail || !projectId) return
    await api(`/projects/${projectId}/runs/${detail.id}/cancel`, { method: 'POST' }).catch(() => {})
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-3xl w-full mx-auto space-y-4">
      <div className="flex gap-2">
        <input className="flex-1 bg-ink-900 border border-ink-600 rounded-md px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder={'Goal for the agent (e.g. "write and run a script that prints the first 10 primes")'}
          value={goal} onChange={(e) => setGoal(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && start()} />
        <button onClick={start} className="bg-accent hover:bg-accent/90 text-white rounded-md px-4 text-sm">Run</button>
      </div>
      {error && <div className="text-sm text-red-400">{error}</div>}
      {detail && (
        <div className="bg-ink-900 border border-ink-700 rounded-lg p-4 text-sm space-y-2">
          <div className="flex justify-between items-center">
            <span className="font-medium">Run #{detail.id}</span>
            <span className="text-accent-bright">{detail.state}</span>
            {['planning', 'debugging (round 1)', 'debugging (round 2)', 'debugging (round 3)'].includes(detail.state) &&
              <button onClick={cancel} className="text-xs text-red-400 hover:text-red-300">Cancel</button>}
          </div>
          {detail.error && <div className="text-red-400">{detail.error}</div>}
          {detail.result && <div className="text-emerald-400">{detail.result}</div>}
          <div className="space-y-1 font-mono text-xs text-slate-400">
            {(detail.steps || []).map((s: any, i: number) => (
              <div key={i} className="border-t border-ink-800 pt-1">
                <span className="text-accent-bright">{s.phase}</span>{' '}
                {s.action ? `${s.action} ${s.detail || ''}` : s.summary || s.command || ''}
                {s.result && !s.result.ok && <span className="text-red-400"> failed</span>}
                {s.result && s.result.stdout && <pre className="whitespace-pre-wrap text-slate-500 pl-3">{s.result.stdout.slice(0, 800)}</pre>}
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="space-y-2">
        {runs.map((r) => (
          <button key={r.id} onClick={() => { setDetail(r); watch(r.id) }}
            className="block w-full text-left bg-ink-900 border border-ink-700 hover:border-accent/60 rounded-lg px-4 py-3 text-sm">
            <span className="text-slate-500 mr-2">#{r.id}</span>{r.goal.slice(0, 80)}
            <span className="float-right text-accent-bright">{r.state}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
