# MOSP Pareto Explorer: Render deployment

Backend and frontend are live. Public health, data APIs, frontend assets and production CORS passed. Browser UI verification is pending because the browser access permission system explicitly denied this site's domain. This document does not claim physical iPhone/Android or production playback verification.

## Live resources

| Resource | Verified URL / ID |
| --- | --- |
| GitHub repository | https://github.com/jockh/MOSP_research |
| Branch | `main` (auto-deploy configured; push trigger verification pending) |
| Frontend | https://taipei-pareto-explorer.onrender.com |
| Static Site ID | `srv-dauukhk1nsns73fptjc0` |
| Backend | https://mosp-taipei-api.onrender.com |
| Web Service ID | `srv-dauuick1nsns73fpl0o0` |
| Health | https://mosp-taipei-api.onrender.com/api/health |
| FastAPI docs | https://mosp-taipei-api.onrender.com/docs |
| Backend plan / region | **free** / Singapore |
| Frontend type | Free Static Site; no paid compute plan |

The existing unrelated Render service was not changed. No paid service, disk, database, worker, or other paid resource was created.

## Architecture and canonical root

The Git repository root is `MOSP_research/`. React/Vite static assets are served by Render's CDN. They call the separate FastAPI Web Service over HTTPS. The backend reads the committed research CSVs; deployment does not execute MOSP experiments or regenerate results.

The backend's Root Directory is the **repository root**, because `src/`, `data/` and `results/` must be available. Render excludes files outside the configured Root Directory from build/runtime. Do not select only the nested backend directory.

Every backend data/result path uses `pathlib` and `__file__` via `src.paths`. Relative `PARETO_CSV` or `STATION_POSITION_CSV` overrides resolve against the canonical root. Normal deployment needs no overrides. Committed runtime data includes all existing formal `data/taipei_metro/` inputs, its separate station-coordinate CSV, and `results/experiment_05_all_od/all_od_pareto_routes.csv`.

Health diagnostics expose repository-relative dataset names; full unexpected exceptions are logged server-side. The route-state model, Circular Line coordinate fallback, route ordering, API cost values and research CSV contents are unchanged.

## Backend configuration

| Setting | Actual value |
| --- | --- |
| Root Directory | Empty (repository root) |
| Build Command | `python -m pip install -e . -r web/taipei-pareto-explorer/backend/requirements.txt` |
| Start Command | `python -m uvicorn main:app --app-dir web/taipei-pareto-explorer/backend --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/health` |
| `PYTHON_VERSION` | `3.13.15` |
| `FRONTEND_ORIGIN` | `https://taipei-pareto-explorer.onrender.com` |

Root `.python-version` pins the same tested version. `pip install -e .` installs the canonical `src`, `experiments`, `validation` and `analysis` packages without `sys.path` edits. Backend requirements pin FastAPI, Uvicorn with standard extras, pandas, requests and python-dotenv; research package dependencies are installed through root `pyproject.toml` in the same pip transaction.

Render provides `$PORT`. Use the Linux-shell start command above and bind `0.0.0.0`; do not use `--reload` in production. The committed CSVs are read-only; the optional existing coordinate cache is disposable, and no persistent disk is needed.

CORS permits the exact origin configured in `FRONTEND_ORIGIN` plus `http://localhost:5173`. Unexpected origins and `http://127.0.0.1:5173` are not allowed. Additional custom frontend origins can be comma-separated explicitly. CORS is not API authentication: public GET endpoints are deliberately public research data.

## Frontend configuration

| Setting | Actual value |
| --- | --- |
| Root Directory | `web/taipei-pareto-explorer/frontend` |
| Build Command | `npm ci && npm run build` |
| Publish Directory | `dist` |
| `NODE_VERSION` | `24.19.0` |
| `SKIP_INSTALL_DEPS` | `true` (the build command runs npm ci itself) |
| `VITE_API_BASE_URL` | `https://mosp-taipei-api.onrender.com` |

`dist` is relative to the frontend Root Directory. All four API calls use `import.meta.env.VITE_API_BASE_URL`; endpoints retain their `/api/...` paths. Trailing slashes are normalized. This non-secret value is embedded at **build time**; rebuild the Static Site after changing it. Never place secrets in `VITE_` variables.

The empty local fallback sends same-origin `/api` requests through Vite's development/preview proxy to localhost port 8000. That proxy also supports phones opening the frontend's LAN URL. Render Static Sites do not run Vite's proxy, so production must have the real HTTPS backend origin configured. `MOSP_API_PROXY_TARGET` is local server configuration only. The app currently has no client-side URL routes, so its existing root page needs no SPA rewrite.

## Local reproduction

Use an activated Python 3.13 environment from the canonical root:

```powershell
python -m pip install -e . -r web/taipei-pareto-explorer/backend/requirements.txt
python -c "import src; print(src.__file__)"
python -c "from src.graph import Graph; from src.mosp import mosp; print('Graph OK; MOSP OK')"
python -m uvicorn main:app --app-dir web/taipei-pareto-explorer/backend --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd web/taipei-pareto-explorer/frontend
npm ci
npm run build
npm run dev -- --host 0.0.0.0
```

Leave local `VITE_API_BASE_URL` empty. `.env.example` templates are supplied. For physical phone testing, permit the frontend port through the local firewall/network; backend traffic goes through the frontend proxy.

For correctness validation without overwriting formal research outputs, use a separate output location:

```powershell
$env:MOSP_RESULTS_DIR = 'regression/runs'
python -m validation.test_correctness
```

This preserves all 1000 cases, 7 nodes, objectives 2–5, cost range 1–20 and seed 20260930. It changes the output directory only.

## Redeploy and monitor

Global GitHub/Render CLI commands are used; no stored token, password or API key is committed. Authenticate only through `gh auth login` and `render login` when needed.

```powershell
gh auth status
render workspace current --output json
git status
git diff
git add <reviewed-files>
git commit -m "Describe the production fix"
git push origin main
render deploys list srv-dauuick1nsns73fpl0o0 --output json
render deploys list srv-dauukhk1nsns73fptjc0 --output json
render logs --resources srv-dauuick1nsns73fpl0o0 --limit 100 --output json
```

Both services have `autoDeployTrigger: commit` configured, but the native push trigger has **not been verified**. A push changing both services' environment examples did not trigger a new deploy during ten minutes of monitoring. The user completed GitHub repository authorization; reconnecting the same repository with the CLI did not resolve this. Existing Git Credentials must be checked in the Render Dashboard. Dashboard access is currently denied by the browser permission system. Until this is resolved, explicitly deploy each pushed revision and verify it becomes **live**, inspect build/runtime logs, then test health and the frontend. Manual redeploy: `render deploys create SERVICE_ID --output json --confirm`.

Environment-variable changes require redeployment; frontend build-time variables require a rebuild. The production CORS variable was updated with Render's official single-variable API, preserving other variables, then the backend was redeployed and verified. Never expose CLI credentials in logs/chat or source code.

## Blueprint / infrastructure record

Root `render.yaml` records the actual services, commands and public environment values, using Render's official schema. `render blueprints validate render.yaml --output json` returned **valid: true**. It was validated but not applied, to avoid creating duplicate resources alongside the CLI-created services.

The backend explicitly uses `plan: free`; the frontend uses `type: web`, `runtime: static` and has no plan field. If reproducing in a different workspace, obtain its actual returned service URLs and update the two public origin variables; URL suffixes are not assumed. Do not choose a paid resource if free capacity is unavailable.

## Verification and troubleshooting

- Local correctness: **1000 passed / 0 failed**, 7481 simple paths; unchanged research settings.
- Fresh Python 3.13 editable install, canonical imports from an external cwd and `pip check`: passed.
- Local `npm ci`, production build and environment injection: passed.
- Render backend and frontend builds/runtime: live; logs captured.
- Public frontend HTML/JS: HTTP 200; compiled API base equals the actual HTTPS backend; no localhost backend URLs.
- Public health: HTTP 200, `ok: true`, `pareto_csv_found: true`, 119 model stations matched, zero missing coordinates.
- Public stations/network/routes: HTTP 200; response bytes equal the pre-change local API.
- 東湖站 → 中原站: **5 Pareto routes**, unchanged costs.
- Production origin and localhost:5173 CORS/preflight: allowed. Unexpected origins and 127.0.0.1:5173: denied.
- 87 core/model/input/formal-result files: SHA-256 unchanged.
- Production browser interactions/console/responsive matrix: **pending browser access permission**. Physical iPhone Safari, Android Chrome and iPad Safari remain pending; Chromium viewport checks do not establish real Safari compatibility.

Evidence is in `regression/deployment/verification.json` and associated logs. Responsive implementation/limitations are recorded in `RESPONSIVE_REPORT.md`.

If imports fail, confirm repository-root build scope and editable installation in the same interpreter as Uvicorn. If files are missing, confirm the formal CSVs are tracked; no local absolute path is required. If the frontend reports fetch/CORS errors, verify `VITE_API_BASE_URL`, rebuild, verify `FRONTEND_ORIGIN`, redeploy backend, then inspect network/console and logs. Mixed content means an HTTP API origin was configured under the HTTPS site.

The health endpoint retains its diagnostic HTTP-200 behavior even when JSON reports `ok: false`; always check both JSON booleans rather than treating HTTP status alone as readiness. Free Web Services can sleep after inactivity and take time on the next request. Free-tier usage allowances apply; no paid resource or upgrade was authorized or created.

Did deployment change any MOSP algorithm, experimental setting, Taipei Metro assumption, or research result? **No.**

References: [Render FastAPI](https://render.com/docs/deploy-fastapi), [monorepo root scope](https://render.com/docs/monorepo-support), [Static Sites](https://render.com/docs/static-sites), [CLI deployment](https://render.com/docs/your-first-deploy), [single environment variable API](https://api-docs.render.com/reference/update-env-var), [Vite environment variables](https://vite.dev/guide/env-and-mode.html).
