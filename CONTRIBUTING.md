# Contributing to Foe Agent

1. Fork, branch (`feat/your-change`), commit.
2. Backend: `pip install -r requirements.txt -r requirements-dev.txt && python -m pytest tests -q` must pass.
3. Frontend: `npm install && npm run build` must pass (type checks are part of the build).
4. Keep security invariants: never execute commands outside the sandbox runner, never return another user's data, never ship API keys to the browser.
5. Open a pull request describing what changed and how you verified it.
