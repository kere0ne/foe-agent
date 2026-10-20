# Architecture

```
frontend (React+Vite+Tailwind, dark UI)
   |  /api (Vite dev proxy or same-origin /api mount)
backend (FastAPI)
   |-- auth: bcrypt + JWT, ownership checks on every resource
   |-- routers: auth, projects, files, models, conversations/chat, runs
   |-- llm/providers.py: Ollama (native) + OpenAI-compatible streaming clients
   |-- agent/runner.py: state machine PLAN -> INSPECT -> ACT -> OBSERVE -> DEBUG -> VERIFY -> COMPLETE
   |-- agent/tools.py: write_file (path-checked), run_command (subprocess, timeout, scrubbed env)
   |-- services/files.py: per-project root, traversal-safe joins, tree, safe zip extraction
storage:
   |-- Postgres: users, projects, conversations, messages, model_providers, agent_runs (+ step log as JSON checkpoints)
   |-- disk: ./data/projects/<project_id>/ (per-user isolated workspaces)
```

Key decisions:
- Every project owns a real directory; agent tool calls are constrained to it by resolved-path checks.
- Run state (plan, each tool result, verify outcome) is appended to the `agent_runs.steps` JSON column after every phase, so a crashed worker leaves an inspectable checkpoint trail. Resume-from-checkpoint is not implemented yet (ROADMAP).
- Streaming chat is SSE; the agent runner is a background task per run with a cancel flag checked between steps.
- The frontend never sees provider API keys, only `has_key`.
