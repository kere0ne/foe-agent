# Security Policy

## Reporting
Open a private security advisory via GitHub (Security tab) rather than a public issue.

## Current design boundaries (read before deploying)
- Auth is JWT bearer with bcrypt-hashed passwords; tokens expire in 7 days.
- Every project/file/run endpoint checks ownership server-side; users cannot read or write each other's projects.
- Uploaded archives are checked for path traversal (no absolute paths, no `..`, size and file-count caps).
- Agent commands run through a subprocess runner scoped to the project directory with a timeout, a scrubbed environment, and no shell profile. This is process isolation, NOT a container: do not expose the sandbox to untrusted users until the container runtime (docs/SANDBOX.md) is enabled.
- Model API keys are stored server-side in Postgres and never sent to the browser (the API returns only a `has_key` boolean). Set `FOE_JWT_SECRET` to a real random value in production.
- Treat everything a model produces as untrusted input, the same as uploads.
