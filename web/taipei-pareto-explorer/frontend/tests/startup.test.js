import assert from 'node:assert/strict';
import test from 'node:test';
import {
  loadInitialData,
  STARTUP_MAX_WAIT_MS,
  STARTUP_RETRY_INTERVAL_MS,
  STARTUP_REQUEST_TIMEOUT_MS,
} from '../src/startup.js';

const health = { ok: true, pareto_csv_found: true };
const stations = { stations: ['東湖站', '中原站'] };
const network = { stations: [{ id: '東湖站' }, { id: '中原站' }] };
const routes = { routes: [{ id: 'unchanged-fixture' }] };
const readyApi = overrides => ({
  getHealth: async () => health,
  getStations: async () => stations,
  getNetwork: async () => network,
  getRoutes: async () => routes,
  ...overrides,
});
const options = overrides => ({
  origin: '東湖站', destination: '中原站',
  signal: new AbortController().signal,
  maxWaitMs: 1000, retryIntervalMs: 3, requestTimeoutMs: 30,
  ...overrides,
});

test('production waits are bounded: 3 minutes, 3-second retry, 12-second request', () => {
  assert.equal(STARTUP_MAX_WAIT_MS, 180_000);
  assert.equal(STARTUP_RETRY_INTERVAL_MS, 3_000);
  assert.equal(STARTUP_REQUEST_TIMEOUT_MS, 12_000);
});

test('warm startup loads the selected OD once and returns data without transforming it', async () => {
  let routeRequests = 0;
  const result = await loadInitialData(readyApi({
    getRoutes: async (origin, destination, { signal }) => {
      assert.equal(origin, '東湖站');
      assert.equal(destination, '中原站');
      assert.equal(signal.aborted, false);
      routeRequests += 1;
      return routes;
    },
  }), options());
  assert.deepEqual(result, { health, stations, network, routes });
  assert.equal(result.routes, routes);
  assert.equal(routeRequests, 1);
});

test('first network errors retry automatically and later succeed', async () => {
  let healthRequests = 0;
  let metadataRequests = 0;
  const progress = [];
  const result = await loadInitialData(readyApi({
    getHealth: async () => {
      healthRequests += 1;
      if (healthRequests < 3) throw new TypeError('Failed to fetch');
      return health;
    },
    getStations: async () => { metadataRequests += 1; return stations; },
  }), options({ onProgress: state => progress.push(state) }));
  assert.equal(result.routes, routes);
  assert.equal(healthRequests, 3);
  assert.equal(metadataRequests, 1);
  assert.deepEqual(progress.filter(s => s.phase === 'retrying').map(s => s.attempt), [1, 2]);
});

test('health HTTP success alone does not enable data loading: both booleans must be true', async () => {
  const responses = [{ ok: false, pareto_csv_found: true }, { ok: true, pareto_csv_found: false }, health];
  let metadataRequests = 0;
  await loadInitialData(readyApi({
    getHealth: async () => responses.shift(),
    getNetwork: async () => { assert.equal(responses.length, 0); metadataRequests += 1; return network; },
  }), options());
  assert.equal(metadataRequests, 1);
});

test('a hanging health/JSON operation times out, then automatically recovers', async () => {
  let attempts = 0;
  let firstSignal;
  const result = await loadInitialData(readyApi({
    getHealth: ({ signal }) => {
      attempts += 1;
      if (attempts === 1) { firstSignal = signal; return new Promise(() => {}); }
      return Promise.resolve(health);
    },
  }), options({ requestTimeoutMs: 15 }));
  assert.equal(firstSignal.aborted, true);
  assert.equal(attempts, 2);
  assert.equal(result.network, network);
});

test('a transient routes error retries the entire batch and cancels its hanging sibling', async () => {
  let routeRequests = 0;
  let networkRequests = 0;
  let firstNetworkSignal;
  const result = await loadInitialData(readyApi({
    getNetwork: ({ signal }) => {
      networkRequests += 1;
      if (networkRequests === 1) { firstNetworkSignal = signal; return new Promise(() => {}); }
      assert.equal(firstNetworkSignal.aborted, true);
      return Promise.resolve(network);
    },
    getRoutes: async () => {
      routeRequests += 1;
      if (routeRequests === 1) throw new Error('HTTP 503');
      return routes;
    },
  }), options());
  assert.equal(firstNetworkSignal.aborted, true);
  assert.equal(routeRequests, 2);
  assert.equal(result.routes, routes);
});

test('missing metadata is retried before publishing a ready state', async () => {
  let requests = 0;
  const result = await loadInitialData(readyApi({
    getStations: async () => ++requests === 1 ? {} : stations,
  }), options());
  assert.equal(requests, 2);
  assert.equal(result.stations, stations);
});

test('permanent failure stops at the total deadline and a fresh manual attempt can succeed', async () => {
  let requests = 0;
  const start = performance.now();
  await assert.rejects(loadInitialData(readyApi({
    getHealth: async () => { requests += 1; throw new TypeError('Failed to fetch'); },
  }), options({ maxWaitMs: 60 })), /Startup wait limit reached/);
  assert.ok(performance.now() - start < 300, 'total deadline must bound retries');
  const stoppedRequests = requests;
  await new Promise(resolve => setTimeout(resolve, 10));
  assert.equal(requests, stoppedRequests);
  const result = await loadInitialData(readyApi(), options());
  assert.equal(result.routes, routes);
});

test('a hanging request cannot exceed the total deadline even if its own timeout is longer', async () => {
  let requestSignal;
  const start = performance.now();
  await assert.rejects(loadInitialData(readyApi({
    getHealth: ({ signal }) => { requestSignal = signal; return new Promise(() => {}); },
  }), options({ maxWaitMs: 40, requestTimeoutMs: 500 })), /Startup wait limit reached/);
  assert.ok(performance.now() - start < 300);
  assert.equal(requestSignal.aborted, true);
});

test('effect cleanup cancels a pending fetch without retrying (StrictMode/unmount)', async () => {
  const controller = new AbortController();
  let requestSignal;
  let attempts = 0;
  const pending = loadInitialData(readyApi({
    getHealth: ({ signal }) => {
      attempts += 1;
      requestSignal = signal;
      queueMicrotask(() => controller.abort());
      return new Promise(() => {});
    },
  }), options({ signal: controller.signal }));
  await assert.rejects(pending, { name: 'AbortError' });
  assert.equal(requestSignal.aborted, true);
  assert.equal(attempts, 1);
});

test('effect cleanup cancels a retry wait and does not start another request', async () => {
  const controller = new AbortController();
  let attempts = 0;
  const pending = loadInitialData(readyApi({
    getHealth: async () => { attempts += 1; throw new TypeError('Failed to fetch'); },
  }), options({
    signal: controller.signal,
    retryIntervalMs: 100,
    onProgress: state => {
      if (state.phase === 'retrying') setTimeout(() => controller.abort(), 5);
    },
  }));
  await assert.rejects(pending, { name: 'AbortError' });
  await new Promise(resolve => setTimeout(resolve, 10));
  assert.equal(attempts, 1);
});
