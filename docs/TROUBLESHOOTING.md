# Troubleshooting

- "Could not reach http://...: check the base URL and that the server is running" - Ollama not running or wrong port. `curl http://localhost:11434/api/tags` should return JSON.
- "model 'x' is not pulled on that Ollama server" - run `ollama pull x`.
- Agent run fails at plan step with JSON errors - the model is too small for structured output; use at least an 8B instruct model (llama3.1:8b, qwen2.5:7b) or any hosted instruct model.
- Run stuck in queued - check backend logs; the run executes as a background task in the API process.
- CORS errors in the browser console - add your frontend origin to `FOE_CORS_ORIGINS`.
- 401 loops - token expired (7 days); sign in again.
