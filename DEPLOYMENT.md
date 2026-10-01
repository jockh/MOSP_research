# Render deployment guide

Status: local deployment preparation and smoke tests passed. Full public deployment is now authorized; GitHub/Render CLI authentication is complete; public deployment is in progress. No public services have been created yet.

This guide assumes the Git repository root is **MOSP_research/**, containing `pyproject.toml`, `src/`, `data/`, `results/`, and `web/`. Preserve the formal CSVs in Git; neither backend installation nor deployment regenerates research results.

## 1. Review the repository

Commit the deployment changes and required input/output files to the repository you intend to connect to Render. Exclude `.venv/`, `node_modules/`, `.env*` secrets, caches, and generated build output. `.env.example` templates may be committed. Do not remove the original projects while preparing this repository. The canonical root is now initialized on Git branch `main`; it has no remote or commit until authenticated GitHub account/repository discovery is completed.

Required runtime files include:

- `results/experiment_05_all_od/all_od_pareto_routes.csv`
- All existing formal Taipei Metro inputs in `data/taipei_metro/`
- `data/taipei_metro/taipei_metro_station_positions.csv`
- The canonical `src` package and root `pyproject.toml`

All backend file paths are anchored to `Path(__file__)` through `src.paths`; relative environment overrides resolve against the canonical project root. There are no workstation-specific data paths or `os.getcwd()` dependencies in the backend. The local coordinate CSV avoids a download during normal startup.

## 2. Backend: Render Web Service

Connect the repository and choose the Python runtime. Use:

| Setting | Value |
| --- | --- |
| Root Directory | Leave blank (canonical repository root) |
| Build Command | `python -m pip install -e . -r web/taipei-pareto-explorer/backend/requirements.txt` |
| Start Command | `python -m uvicorn main:app --app-dir web/taipei-pareto-explorer/backend --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/health` |
| Environment | `PYTHON_VERSION=3.13.15` |
| Environment | `FRONTEND_ORIGIN=https://YOUR-FRONTEND.onrender.com` |

The root `.python-version` also pins 3.13.15. The requirements pin FastAPI, Uvicorn with standard extras, pandas, requests, and python-dotenv. Editable installation installs the canonical research package and its declared dependencies; it fixes `from src.paths import ...` without changing `sys.path`.

**Do not set backend Root Directory to `web/taipei-pareto-explorer/backend`.** Render excludes files outside the configured Root Directory from build/runtime; that would hide `src`, `data`, and `results`. If your Git repository instead has an outer `MOSP_project/` root, set backend Root Directory to `MOSP_research` and frontend Root Directory to `MOSP_research/web/taipei-pareto-explorer/frontend`; commands above remain relative to the canonical root.

Render supplies `$PORT`; the command is for Render's Linux shell. Do not use `--reload` in production. No persistent disk is needed for the committed, read-only research CSVs. The existing optional coordinate cache is disposable; canonical local coordinate data is supplied.

`FRONTEND_ORIGIN` accepts one origin (or comma-separated origins for an additional custom domain). Include scheme and hostname, omit URL paths. Only `http://localhost:5173` is always allowed for local development, alongside the origins configured in `FRONTEND_ORIGIN`. Unknown origins receive no CORS allow-origin header; wildcard origins are not accepted. CORS changes require a backend restart/redeploy.

## 3. Frontend: Render Static Site

Use the same repository and configure:

| Setting | Value |
| --- | --- |
| Root Directory | `web/taipei-pareto-explorer/frontend` |
| Build Command | `npm ci && npm run build` |
| Publish Directory | `dist` |
| Environment | `NODE_VERSION=24.19.0` |
| Environment | `VITE_API_BASE_URL=https://YOUR-BACKEND.onrender.com` |

The frontend `.node-version` also pins the tested Node version. The lockfile is supplied for `npm ci`. `dist` is relative to the frontend Root Directory.

Set `VITE_API_BASE_URL` **before building** to the backend's actual HTTPS origin, without `/api`. All four frontend API calls append their existing `/api/...` paths. Trailing slashes are normalized. This public variable is embedded in JavaScript at build time; rebuild the static site whenever its value changes. Never put secrets in a `VITE_` variable.

An empty value intentionally supports local Vite development/preview through the `/api` proxy. **Render Static Sites do not run that Vite proxy**, so a production site must have the backend URL configured. Neither a localhost URL nor `MOSP_API_PROXY_TARGET` should be configured on the Static Site. HTTPS prevents mixed-content requests from the HTTPS frontend.

The current app has no client-side URL routes; no SPA rewrite is needed for its existing root page. If client-side routing is added later, add Render's `/*` → `/index.html` rewrite. Do not rewrite API calls to HTML.

## 4. Connect the two services when you choose to deploy

1. Create the backend Web Service with the settings above and record its HTTPS URL.
2. Create the Static Site with that URL in `VITE_API_BASE_URL`, then record the frontend HTTPS URL.
3. Set the backend `FRONTEND_ORIGIN` to the exact frontend origin and restart/redeploy the backend.
4. For a custom domain, update the frontend API origin if needed and include the frontend custom-domain origin in CORS.
5. Verify health, browser requests and route display before announcing availability.

These steps will be executed automatically after CLI authentication. Only free resources are authorized; if a free Web Service or free Static Site is unavailable, stop rather than select a paid plan. Do not delete existing resources or force-push.

## 5. Local installation and smoke tests

From the canonical repository root, using an activated Python 3.13 environment:

```powershell
python -m pip install -e . -r web/taipei-pareto-explorer/backend/requirements.txt
python -c "import src; from src.paths import PROJECT_ROOT; print(src.__file__); print(PROJECT_ROOT)"
python -m uvicorn main:app --app-dir web/taipei-pareto-explorer/backend --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd web/taipei-pareto-explorer/frontend
npm ci
npm run build
npm run dev -- --host 0.0.0.0
```

Leave local `VITE_API_BASE_URL` empty to use the proxy. Optionally set `MOSP_API_PROXY_TARGET` when the local backend uses another port. Phones opening the frontend's LAN URL then request the frontend's `/api`, rather than the phone's localhost. Local phone access requires the host firewall/network to permit the frontend port.

Check `http://127.0.0.1:8000/api/health`:

```json
{"ok": true, "pareto_csv_found": true}
```

The endpoint includes existing coordinate/file diagnostics as well. Check the JSON booleans, not only HTTP 200: its existing diagnostic behavior returns HTTP 200 even if the JSON reports `ok: false`. In that case check committed files, environment overrides and logs. The route lookup endpoint remains `/api/routes?origin=東湖站&destination=中原站`.

## 6. Deployment verification checklist

- Backend `/api/health` reports both booleans true and no missing station coordinates.
- The Static Site loads with no console/CORS/mixed-content errors.
- Requests go to the configured backend HTTPS origin and return JSON.
- Stations, the complete network and the existing five 東湖站 → 中原站 routes display.
- Playback, route cards and the tradeoff plot remain synchronized.
- Validate iPhone Safari and Android Chrome on physical devices, including browser address-bar expansion/collapse, safe areas, native selects, touch zoom/pan and portrait/landscape. Local Chromium viewport checks do not establish real iOS Safari compatibility.

## 7. Verification evidence and limits

See `regression/deployment/verification.json` for installation, frontend build, environment injection, backend import/path, live HTTP health/CORS and protected-file checks. See `RESPONSIVE_REPORT.md` for responsive viewport checks and physical-device checks still pending.

No MOSP algorithm, Taipei Metro model, Pareto route data, or formal research result is changed by deployment configuration. Health diagnostics expose repository-relative dataset names instead of absolute workstation paths; unexpected errors go to backend logs. Local smoke tests do not certify Render's Linux runtime or an actual hosted service; those are verified after you authorize deployment.

References: [Render FastAPI](https://render.com/docs/deploy-fastapi), [Render monorepos](https://render.com/docs/monorepo-support), [Render Static Sites](https://render.com/docs/static-sites), [Python versions](https://render.com/docs/python-version), [Node versions](https://render.com/docs/node-version), [Vite environment variables](https://vite.dev/guide/env-and-mode.html).

## 8. Authentication and continuation

Official Git 2.56.0, GitHub CLI 2.102.0 and Render CLI 2.28.0 were installed from their upstream release assets with SHA-256 checks. Their user PATH folders are under `%LOCALAPPDATA%/MOSPDeploymentTools`. Five official Render skills are installed for Codex under the user's `.agents/skills/` directory.

In a new PowerShell, complete only the two required logins:

```powershell
& "$env:LOCALAPPDATA\MOSPDeploymentTools\gh\bin\gh.exe" auth login
& "$env:LOCALAPPDATA\MOSPDeploymentTools\render\render.exe" login
```

Choose HTTPS for GitHub and complete browser authorization. Choose your Render workspace when prompted. Do not paste credentials into chat, source files, or `render.yaml`.

After authentication, the remaining automatic steps are: discover/reuse the correct GitHub repository (create a public repository only if absent); derive commit author from the authenticated account; review/stage/commit/push `main`; create a free backend and verify its actual returned HTTPS URL; create a free Static Site using that URL; configure CORS with the actual frontend origin; redeploy and wait for both services to be live; verify public API and browser interactions; record actual IDs/URLs and a validated `render.yaml`; commit/push final deployment documentation; verify clean Git status. No URLs or deploy statuses are assumed in advance.

Actual GitHub URL, backend URL, frontend URL, service IDs, production build/runtime logs, free-plan eligibility and Blueprint validation remain **pending resource creation/deployment**. This repository must not be described as deployed until those checks succeed.
