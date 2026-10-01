export const STARTUP_MAX_WAIT_MS = 180_000;
export const STARTUP_RETRY_INTERVAL_MS = 3_000;
export const STARTUP_REQUEST_TIMEOUT_MS = 12_000;

const aborted = () => new DOMException('Startup cancelled', 'AbortError');
const expired = () => new Error('Startup wait limit reached');

function checkCancellation(signal) {
  if (signal?.aborted) throw aborted();
}

// Bound the whole request, including JSON parsing, and cancel it on cleanup.
async function requestWithTimeout(request, signal, timeoutMs) {
  checkCancellation(signal);
  const controller = new AbortController();
  const cancel = () => controller.abort();
  signal.addEventListener('abort', cancel, { once: true });
  let rejectOnAbort;
  const cancelled = new Promise((_, reject) => {
    rejectOnAbort = () => reject(aborted());
    controller.signal.addEventListener('abort', rejectOnAbort, { once: true });
  });
  const timer = setTimeout(cancel, timeoutMs);
  try {
    return await Promise.race([
      Promise.resolve().then(() => request({ signal: controller.signal })),
      cancelled,
    ]);
  } finally {
    clearTimeout(timer);
    signal.removeEventListener('abort', cancel);
    controller.signal.removeEventListener('abort', rejectOnAbort);
    controller.abort();
  }
}

function wait(ms, signal) {
  checkCancellation(signal);
  return new Promise((resolve, reject) => {
    const cancel = () => {
      clearTimeout(timer);
      reject(aborted());
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', cancel);
      resolve();
    }, ms);
    signal?.addEventListener('abort', cancel, { once: true });
  });
}

// Startup alone retries. Subsequent searches and route animation stay unchanged.
export async function loadInitialData(api, {
  origin,
  destination,
  signal,
  onProgress = () => {},
  maxWaitMs = STARTUP_MAX_WAIT_MS,
  retryIntervalMs = STARTUP_RETRY_INTERVAL_MS,
  requestTimeoutMs = STARTUP_REQUEST_TIMEOUT_MS,
}) {
  const deadline = performance.now() + maxWaitMs;
  let attempt = 0;
  while (performance.now() < deadline) {
    checkCancellation(signal);
    attempt += 1;
    onProgress({ phase: 'connecting', attempt });
    const controller = new AbortController();
    const cancel = () => controller.abort();
    signal?.addEventListener('abort', cancel, { once: true });
    const request = callback => {
      const remaining = deadline - performance.now();
      if (remaining <= 0) throw expired();
      return requestWithTimeout(callback, controller.signal, Math.min(requestTimeoutMs, remaining));
    };
    try {
      const health = await request(api.getHealth);
      if (!health.ok || !health.pareto_csv_found) throw new Error('Backend data not ready');
      onProgress({ phase: 'loading', attempt });
      const [stations, network, routes] = await Promise.all([
        request(api.getStations),
        request(api.getNetwork),
        request(options => api.getRoutes(origin, destination, options)),
      ]);
      if (!Array.isArray(stations.stations) || !stations.stations.length ||
          !Array.isArray(network.stations) || !network.stations.length ||
          !Array.isArray(routes.routes)) {
        throw new Error('Initial data not ready');
      }
      checkCancellation(signal);
      if (performance.now() >= deadline) throw expired();
      return { health, stations, network, routes };
    } catch {
      checkCancellation(signal);
      // Stop sibling requests before the next attempt; do not overlap batches.
      controller.abort();
      const remaining = deadline - performance.now();
      if (remaining <= 0) throw expired();
      onProgress({ phase: 'retrying', attempt });
      await wait(Math.min(retryIntervalMs, remaining), signal);
    } finally {
      signal?.removeEventListener('abort', cancel);
      controller.abort();
    }
  }
  checkCancellation(signal);
  throw expired();
}
