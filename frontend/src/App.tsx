import React, { useEffect, useState } from 'react'
import { api, getToken, clearToken } from './api'
import AuthView from './views/AuthView'
import ChatView from './views/ChatView'
import ProjectsView from './views/ProjectsView'
import RunsView from './views/RunsView'
import SettingsView from './views/SettingsView'

type View = 'chat' | 'projects' | 'runs' | 'settings'

export default function App() {
  const [user, setUser] = useState<any>(null)
  const [view, setView] = useState<View>('chat')
  const [conversations, setConversations] = useState<any[]>([])
  const [activeConversation, setActiveConversation] = useState<number | null>(null)
  const [projectId, setProjectId] = useState<number | null>(null)
  const [providerId, setProviderId] = useState<number | null>(null)

  useEffect(() => {
    if (!getToken()) return
    api('/auth/me').then(setUser).catch(() => clearToken())
    refreshConversations()
  }, [])

  async function refreshConversations() {
    try { setConversations(await api('/conversations')) } catch { /* silent */ }
  }

  if (!user) return <AuthView onAuthed={(u) => { setUser(u); refreshConversations() }} />

  return (
    <div className="flex h-full">
      <aside className="w-60 shrink-0 border-r border-ink-700 bg-ink-900 flex flex-col">
        <div className="px-4 py-4 border-b border-ink-700">
          <div className="font-semibold text-accent-bright">Foe Agent</div>
          <div className="text-xs text-slate-500 truncate">{user.email}</div>
        </div>
        <nav className="flex flex-col p-2 gap-1 text-sm">
          {([['chat', 'Chats'], ['projects', 'Projects'], ['runs', 'Agent runs'], ['settings', 'Models & settings']] as [View, string][])
            .map(([v, label]) => (
              <button key={v} onClick={() => setView(v)}
                className={`text-left px-3 py-2 rounded-md ${view === v ? 'bg-ink-700 text-white' : 'hover:bg-ink-800 text-slate-300'}`}>
                {label}
              </button>
            ))}
        </nav>
        <div className="px-3 text-xs uppercase tracking-wide text-slate-500 mt-2">Conversations</div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((c) => (
            <button key={c.id} onClick={() => { setActiveConversation(c.id); setView('chat') }}
              className={`block w-full text-left px-3 py-2 rounded-md text-sm truncate ${activeConversation === c.id ? 'bg-ink-700 text-white' : 'hover:bg-ink-800 text-slate-300'}`}>
              {c.title}
            </button>
          ))}
        </div>
        <button onClick={() => { clearToken(); window.location.reload() }}
          className="m-2 px-3 py-2 text-sm text-slate-400 hover:text-white rounded-md hover:bg-ink-800 text-left">
          Sign out
        </button>
      </aside>
      <main className="flex-1 min-w-0 flex flex-col">
        {view === 'chat' && <ChatView conversations={conversations} activeConversation={activeConversation}
          setActive={setActiveConversation} refresh={refreshConversations} providerId={providerId} />}
        {view === 'projects' && <ProjectsView projectId={projectId} setProjectId={setProjectId} />}
        {view === 'runs' && <RunsView projectId={projectId} setProjectId={setProjectId} providerId={providerId} />}
        {view === 'settings' && <SettingsView providerId={providerId} setProviderId={setProviderId} />}
      </main>
    </div>
  )
}
