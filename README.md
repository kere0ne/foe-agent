# Foe Agent

An open-source autonomous AI software engineering platform: an agent that plans, inspects, writes code, runs commands, diagnoses failures, and verifies its own results, backed by your own models (Ollama, llama.cpp, any OpenAI-compatible endpoint) and your own infrastructure.

**Status: Phase 1 complete (foundation).** See docs/ROADMAP.md for what is real vs pending.

## What works today (verified by the test suite)
- Accounts: register/login with bcrypt + JWT, rate limiting on auth endpoints.
- Projects: per-user workspaces with isolated on-disk folders.
- Files API: read, write, delete, tree, safe zip upload (path-traversal checked), download.
- Agent runs: the PLAN -> INSPECT -> ACT -> OBSERVE -> DEBUG -> VERIFY -> COMPLETE loop over real files and real subprocess commands, with per-step checkpointing to Postgres, cancellation, timeouts, and up to 3 debug rounds before failing honestly.
- Model manager: Ollama and OpenAI-compatible providers with real connection tests and actionable errors; keys stay server-side.
- Chat: streaming over SSE with conversation history persisted.
- Frontend: React + TypeScript + Tailwind dark shell (chats, projects, agent runs with live step log, model settings).

## Quick start (Docker)
```bash
cp backend/.env.example .env
# set FOE_JWT_SECRET to: python -c "import secrets; print(secrets.token_hex(32))"
docker compose up --build
# frontend on http://localhost:5173, API on http://localhost:8000/docs
```

## Quick start (local, no Docker)
```bash
# Postgres required
createdb foe
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export FOE_DATABASE_URL="postgresql+asyncpg://foe:foe@localhost:5432/foe"
export FOE_JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
alembic upgrade head
uvicorn app.main:app --reload
# second terminal
cd frontend && npm install && npm run dev
```

## Connect a model (free options)
- Ollama: install from ollama.com, `ollama pull llama3.2:1b`, then add a provider with base URL `http://localhost:11434`, model `llama3.2:1b`.
- llama.cpp / LM Studio / vLLM: any OpenAI-compatible server; base URL like `http://localhost:8080` (the client appends `/v1/chat/completions`).
- Free-tier hosted endpoints (Groq, OpenRouter free models, etc.): same OpenAI-compatible flow, paste the key (it is stored server-side only).

## Tests
```bash
cd backend && python -m pytest tests -q   # 11 tests, uses a throwaway SQLite DB
cd frontend && npm run build              # type-checks and builds
```

## Docs
- docs/ARCHITECTURE.md - system design
- docs/ROADMAP.md - shipped vs pending, honestly labeled
- docs/MODELS.md - provider setup
- docs/SANDBOX.md - execution isolation model and its limits
- docs/DEPLOYMENT.md - production notes
- docs/TROUBLESHOOTING.md - common failures
