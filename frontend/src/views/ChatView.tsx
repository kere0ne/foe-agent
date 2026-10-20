import React, { useEffect, useRef, useState } from 'react'
import { api, streamChat } from '../api'

export default function ChatView({ conversations, activeConversation, setActive, refresh, providerId }: any) {
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => { if (activeConversation) api(`/conversations/${activeConversation}/messages`).then(setMessages).catch(() => {}) }, [activeConversation])
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, streaming])

  async function send() {
    if (!input.trim() || busy) return
    setError('')
    let convoId = activeConversation
    if (!convoId) {
      const convo = await api('/conversations', { method: 'POST', body: { title: input.slice(0, 60) } })
      convoId = convo.id; setActive(convoId)
    }
    const content = input; setInput(''); setMessages((m) => [...m, { role: 'user', content }])
    setBusy(true); setStreaming('')
    await streamChat(convoId, content, providerId || 0,
      (chunk) => setStreaming((s) => s + chunk),
      (err) => setError(err),
      () => {
        setBusy(false)
        setStreaming((s) => { if (s) setMessages((m) => [...m, { role: 'assistant', content: s }]); return '' })
        refresh()
      })
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="flex-1 overflow-y-auto p-6 space-y-4 max-w-3xl w-full mx-auto">
        {messages.length === 0 && !streaming && (
          <div className="text-slate-500 text-sm">Pick a model in Settings, then ask. Foe Agent answers with the model you connect: Ollama, llama.cpp or any OpenAI-compatible endpoint.</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`text-sm leading-relaxed whitespace-pre-wrap rounded-lg px-4 py-3 ${m.role === 'user' ? 'bg-ink-800' : 'bg-ink-900 border border-ink-700'}`}>
            {m.content}
          </div>
        ))}
        {streaming && <div className="text-sm leading-relaxed whitespace-pre-wrap bg-ink-900 border border-ink-700 rounded-lg px-4 py-3">{streaming}</div>}
        {error && <div className="text-sm text-red-400 bg-ink-900 border border-red-900 rounded-lg px-4 py-3">{error}</div>}
        <div ref={bottom} />
      </div>
      <div className="p-4 border-t border-ink-700 max-w-3xl w-full mx-auto flex gap-2">
        <input className="flex-1 bg-ink-900 border border-ink-600 rounded-md px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder={providerId ? 'Message Foe Agent...' : 'Add a model in Settings first'}
          value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }} />
        <button onClick={send} disabled={busy}
          className="bg-accent hover:bg-accent/90 disabled:opacity-50 text-white rounded-md px-4 text-sm">{busy ? '...' : 'Send'}</button>
      </div>
    </div>
  )
}
