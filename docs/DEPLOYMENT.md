# Deployment

## Docker (single host)
`docker compose up --build` runs Postgres, the backend (which runs Alembic then uvicorn), and the frontend. Set `FOE_JWT_SECRET` in `.env`. Mount `foe-data` for project files.

## Render / Railway style platforms
- Backend: root `backend/`, start command `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Provide `FOE_DATABASE_URL` (managed Postgres), `FOE_JWT_SECRET`, `FOE_DATA_DIR` on a persistent disk.
- Frontend: build `npm run build`, serve `dist`, proxy `/api` to the backend (or set the backend to serve `frontend/dist` by copying the build next to it; `app/main.py` mounts it automatically when present).

## Post-deploy checklist
- Health: `GET /api/health`.
- Register an account, add a model, run Test in Settings, then run a trivial agent goal ("write and run a script that prints hello") and confirm state reaches complete with a verify step.
