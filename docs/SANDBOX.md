# Execution isolation

## Today (phase 1)
Agent commands run via `agent/tools.py`: `bash -lc` in a subprocess, cwd pinned to the project directory, environment scrubbed to PATH/HOME(project dir)/LANG, hard timeout (default 180s), output truncated. Network is NOT restricted and the process is NOT containerized. This is fine for a single-user self-host; it is not enough to expose to strangers.

## Planned (phase 2)
The same tools.py interface backed by per-run containers (the repo's docker-compose has a Postgres + backend base ready; the container runtime adds a `foe-sandbox` image with a non-root user, dropped capabilities, no docker socket, and per-run tmpfs). Preview ports will be reached only through an authenticated reverse proxy route, never exposed directly.

Until then: do not host multi-tenant.
