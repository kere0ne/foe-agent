# Model setup

Foe Agent supports two provider kinds. The connection test performs a real HTTP call and reports the actual result; it never pretends a model is available.

## Ollama (free, local)
1. Install Ollama, run `ollama pull llama3.2:1b`.
2. In Settings: kind `Ollama`, base URL `http://localhost:11434`, model `llama3.2:1b`.
The test lists the server's models and warns explicitly if the chosen model is not pulled.

## OpenAI-compatible (llama.cpp, LM Studio, vLLM, Groq, OpenRouter)
Base URL is the root of the API (e.g. `http://localhost:8080`, `https://api.groq.com/openai/v1`); the client appends `/v1/chat/completions` automatically if missing. API keys are optional and stored server-side only.

## Notes
- The agent needs a model that follows JSON instructions reliably; small 1B models often fail to emit the plan JSON, which surfaces as a run failure with the raw model output in the step log.
- Keys live in Postgres (`model_providers.api_key`); the browser only ever receives a boolean.
