# Taipei Pareto Route Explorer

React + Leaflet frontend and FastAPI backend of the canonical MOSP research repository.
The frontend uses the original research data and playback logic, with responsive layout and production API configuration.
No React dependencies belong to the Python research environment.

From the repository root in PowerShell:

```powershell
./web/taipei-pareto-explorer/start_backend.ps1
./web/taipei-pareto-explorer/start_frontend.ps1
```

Backend: http://localhost:8000/api/health. Frontend: http://localhost:5173.
The backend reads `results/experiment_05_all_od/all_od_pareto_routes.csv` and
`data/taipei_metro/taipei_metro_station_positions.csv` via `src.paths`.
It retains the existing coordinate fallback for the Circular Line and optional
environment overrides, anchored to the canonical root. Backend `.env` is local
to the backend directory. Its own virtual environment is supported by the launcher.
The default illustrated OD remains 東湖站 → 中原站.

## Independent backend environment setup

Every new backend virtual environment must install the canonical package as well
as `backend/requirements.txt`. Installing the requirements file alone does not
make `src` importable when starting Uvicorn from the backend directory.
`start_backend.ps1` already performs both installations using the same interpreter.

If using manual commands, run these from the canonical repository root:

```powershell
./web/taipei-pareto-explorer/backend/.venv/Scripts/python.exe -m pip install -e . -r ./web/taipei-pareto-explorer/backend/requirements.txt
./web/taipei-pareto-explorer/backend/.venv/Scripts/python.exe -m uvicorn main:app --app-dir ./web/taipei-pareto-explorer/backend --reload --port 8000
```

Use the backend virtual environment's interpreter for both pip and Uvicorn.
If a reloader is already running after an import failure, stop it with Ctrl+C
and restart it after installation. Data and results still resolve via `src.paths`.

## Production and mobile configuration

Set `VITE_API_BASE_URL` to the backend HTTPS origin at frontend build time. Empty locally uses Vite's `/api` proxy to port 8000, which also supports phones visiting the frontend LAN URL. Set backend `FRONTEND_ORIGIN` to the actual production frontend origin; `http://localhost:5173` remains allowed locally. Example env files are provided. Full Render settings are in the repository-root [DEPLOYMENT.md](../../DEPLOYMENT.md). The backend Root Directory must include `src`, `data`, and `results`.
