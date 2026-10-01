// Render Static Site: set VITE_API_BASE_URL to the backend's HTTPS origin.
// Locally, an empty value uses Vite's /api proxy (default backend: port 8000).
const API = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');
async function json(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
  return body;
}
export const getHealth = options => fetch(`${API}/api/health`, options).then(json);
export const getStations = options => fetch(`${API}/api/stations`, options).then(json);
export const getNetwork = options => fetch(`${API}/api/network`, options).then(json);
export const getRoutes = (origin, destination, options) => {
  const q = new URLSearchParams({origin, destination});
  return fetch(`${API}/api/routes?${q}`, options).then(json);
};
