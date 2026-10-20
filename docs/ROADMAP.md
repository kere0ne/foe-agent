# Roadmap: shipped vs pending

## Phase 1 - SHIPPED (all verified by backend/tests)
- Accounts, projects, files API with traversal protection, safe zip upload
- Agent state machine with real write/run tools, debug loop, cancellation, timeouts, checkpoint log
- Model manager (Ollama + OpenAI-compatible), connection test, server-side keys
- Streaming chat (SSE), conversation persistence
- React dark shell: chats, projects, runs with live step log, model settings
- Alembic migration, Dockerfile, docker-compose (Postgres + backend + frontend), CI workflow, docs

## Phase 2 - PENDING
- Monaco IDE panel with file tree, tabs, diffs, AI edit review (accept/reject)
- WebSocket-based interactive terminal sessions (current commands are one-shot subprocess)
- Live preview with reverse-proxied sandbox ports
- Docker/containerized sandbox runtime behind the same tools.py interface (see docs/SANDBOX.md)

## Phase 3 - PENDING
- Specialized agents (architect, coder, debugger, reviewer, tester) with a coordinator that serializes file access
- Git integration (clone, branch, commit, diff, push, PR) with confirmation gates on push/force operations
- Multi-file zip project import already works; Git clone import pending

## Phase 4 - PENDING
- Resource quotas per user, audit log UI, backup tooling, team/multi-tenant hardening
