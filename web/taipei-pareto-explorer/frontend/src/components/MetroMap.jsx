import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  CircleMarker,
  MapContainer,
  Polyline,
  TileLayer,
  Tooltip,
  useMap,
} from 'react-leaflet';
import { useCompactMap } from '../hooks/useResponsiveViewport.js';

const LINE_COLORS = {
  BR: '#a76528',
  R: '#e3002c',
  G: '#008659',
  O: '#f8b61c',
  BL: '#0070bd',
  Y: '#ffdb00',
};

const lineFamily = raw => {
  const text = String(raw || '').trim();
  const match = text.match(/^([A-Z]+)(?:-\d+)?$/);
  return match ? match[1] : text;
};

// Keep the map focused on the Taipei / New Taipei metro service area.
// This prevents accidental zooming / dragging out to a world view during a demo.
const METRO_MAX_BOUNDS = [
  [24.90, 121.30],
  [25.22, 121.75],
];

const colorForLine = line => LINE_COLORS[lineFamily(line)] || '#94a3b8';
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const ease = t => 1 - Math.pow(1 - t, 3);


// A route panel, rotation, browser toolbar or bfcache restore can resize the
// container without a window resize. Refresh tiles without resetting pan/zoom.
function MapSizeObserver({ compact }) {
  const map = useMap();
  useEffect(() => {
    const container = map.getContainer();
    const viewport = window.visualViewport;
    map.setMinZoom(compact ? 9 : 10.5);
    let frame;
    const schedule = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        if (container.clientWidth && container.clientHeight) {
          map.invalidateSize({ animate: false, pan: true, debounceMoveend: true });
        }
      });
    };
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(schedule);
    observer?.observe(container);
    window.addEventListener('resize', schedule);
    window.addEventListener('orientationchange', schedule);
    window.addEventListener('pageshow', schedule);
    viewport?.addEventListener('resize', schedule);
    schedule();
    return () => {
      cancelAnimationFrame(frame);
      observer?.disconnect();
      window.removeEventListener('resize', schedule);
      window.removeEventListener('orientationchange', schedule);
      window.removeEventListener('pageshow', schedule);
      viewport?.removeEventListener('resize', schedule);
    };
  }, [map, compact]);
  return null;
}

function FitBounds({ coords, token, playing }) {
  const map = useMap();
  const playingRef = useRef(playing);
  playingRef.current = playing;

  useEffect(() => {
    if (!coords?.length) return;

    const points = coords.map(p => [p.lat, p.lon]);

    const container = map.getContainer();
    let userAdjusted = false;
    let timer;
    const fit = (animate = false) => {
      if (points.length === 1) {
        map.setView(points[0], 13);
        return;
      }
      const compact = container.clientWidth < 769 || container.clientHeight < 300;
      map.fitBounds(points, {
        paddingTopLeft: compact ? [60, 55] : [70, 90],
        paddingBottomRight: compact ? [60, 40] : [70, 70],
        maxZoom: 13,
        animate,
        duration: 0.55,
      });
    };
    const markUserAdjusted = () => { userAdjusted = true; };
    const refitAfterResize = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        if (!userAdjusted && !playingRef.current && container.clientWidth && container.clientHeight) fit();
      }, 120);
    };
    fit(true);
    // Refit a default route view on rotation; keep a user-adjusted camera and
    // an ongoing animation untouched when Safari's browser bars resize.
    container.addEventListener('pointerdown', markUserAdjusted, { passive: true });
    container.addEventListener('touchstart', markUserAdjusted, { passive: true });
    container.addEventListener('wheel', markUserAdjusted, { passive: true });
    container.addEventListener('keydown', markUserAdjusted);
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(refitAfterResize);
    observer?.observe(container);
    window.addEventListener('resize', refitAfterResize);
    window.addEventListener('orientationchange', refitAfterResize);
    window.visualViewport?.addEventListener('resize', refitAfterResize);
    return () => {
      clearTimeout(timer);
      observer?.disconnect();
      container.removeEventListener('pointerdown', markUserAdjusted);
      container.removeEventListener('touchstart', markUserAdjusted);
      container.removeEventListener('wheel', markUserAdjusted);
      container.removeEventListener('keydown', markUserAdjusted);
      window.removeEventListener('resize', refitAfterResize);
      window.removeEventListener('orientationchange', refitAfterResize);
      window.visualViewport?.removeEventListener('resize', refitAfterResize);
    };
  }, [map, token]);

  return null;
}

const MetroMap = forwardRef(function MetroMap(
  {
    network,
    routes = [],
    colors = [],
    playing,
    origin,
    destination,
    onStationClick,
    onPlaybackState,
    finalComparison = false,
  },
  ref
) {
  const [active, setActive] = useState(null);
  const [trace, setTrace] = useState([]);
  const [marker, setMarker] = useState(null);
  const [completed, setCompleted] = useState([]);
  const [transfer, setTransfer] = useState(null);
  const [fitCoords, setFitCoords] = useState([]);
  const [fitToken, setFitToken] = useState(0);
  const [visitedStep, setVisitedStep] = useState(-1);
  const [tileError, setTileError] = useState(false);
  const cancelRef = useRef(0);
  const compact = useCompactMap();

  const routeCoords = route =>
    (route?.path || []).filter(p => p.lat != null && p.lon != null);

  const currentStation = routeCoords(active?.route)[visitedStep]?.station;

  const allRouteCoords = useMemo(
    () => routes.flatMap(routeCoords),
    [routes]
  );

  const completedIndexes = useMemo(
    () => new Set(completed.map(item => item.index)),
    [completed]
  );

  const paretoTransferStations = useMemo(() => {
    const names = new Set();

    routes.forEach(route => {
      const coords = routeCoords(route);
      for (let i = 1; i < coords.length; i += 1) {
        const a = coords[i - 1];
        const b = coords[i];
        if (
          a.station === b.station &&
          lineFamily(a.line) !== lineFamily(b.line)
        ) {
          names.add(a.station);
        }
      }
    });

    return names;
  }, [routes]);

  // Physical stations of the currently emphasized route.
  // Duplicate route-state entries at transfer stations are collapsed so the map
  // gets one permanent station label per physical station.
  const routeLabelPoints = useMemo(() => {
    if (!active?.route || finalComparison) return [];

    const coords = routeCoords(active.route);
    const seen = new Set();
    const points = [];

    coords.forEach((point, index) => {
      if (!point?.station || seen.has(point.station)) return;
      seen.add(point.station);
      points.push({
        ...point,
        routeStep: index,
        visited: index <= visitedStep,
        isTransfer: paretoTransferStations.has(point.station),
      });
    });

    return points;
  }, [active, visitedStep, finalComparison, paretoTransferStations]);

  useEffect(() => {
    if (!allRouteCoords.length) return;
    setFitCoords(allRouteCoords);
    setFitToken(x => x + 1);
  }, [routes]);

  function reset() {
    cancelRef.current += 1;
    setActive(null);
    setTrace([]);
    setMarker(null);
    setCompleted([]);
    setTransfer(null);
    setVisitedStep(-1);
    onPlaybackState?.(null);
  }

  function stop() {
    cancelRef.current += 1;
    setMarker(null);
    setTransfer(null);
    onPlaybackState?.(null);
  }

  function fitAll(targetRoutes = routes) {
    const coords = (targetRoutes || []).flatMap(routeCoords);
    if (!coords.length) return;
    setFitCoords(coords);
    setFitToken(x => x + 1);
  }

  function fitRoute(route) {
    const coords = routeCoords(route);
    if (!coords.length) return;
    setFitCoords(coords);
    setFitToken(x => x + 1);
  }

  async function move(a, b, color, runId, duration = 360) {
    const started = performance.now();

    return new Promise(resolve => {
      function frame(now) {
        if (cancelRef.current !== runId) return resolve(false);

        const raw = Math.min(1, (now - started) / duration);
        const t = ease(raw);

        const pos = {
          lat: a.lat + (b.lat - a.lat) * t,
          lon: a.lon + (b.lon - a.lon) * t,
        };

        setMarker({
          ...pos,
          color,
          station: b.station,
        });

        // The last point is the temporary moving endpoint.
        setTrace(prev => [...prev.slice(0, -1), pos]);

        if (raw < 1) {
          requestAnimationFrame(frame);
        } else {
          resolve(true);
        }
      }

      requestAnimationFrame(frame);
    });
  }

  async function playRoute(route, index, color, options = {}) {
    const {
      keepPrevious = false,
      routeNumber = index + 1,
      totalRoutes = 1,
      speed = 2,
      fit = true,
    } = options;

    const runId = ++cancelRef.current;
    const coords = routeCoords(route);

    if (!coords.length) return false;

    // Aim for roughly 4–5 seconds per route at the default 2× speed.
    // Five Pareto alternatives therefore finish in about 20–30 seconds.
    const transitionPairs = coords.slice(1).map((point, i) => [coords[i], point]);
    const transferCount = transitionPairs.filter(([a, b]) => (
      a.station === b.station &&
      lineFamily(a.line) !== lineFamily(b.line)
    )).length;
    const rideCount = Math.max(1, transitionPairs.length - transferCount);
    const targetRouteDuration = 9000 / speed;
    const initialPause = 180 / speed;
    const transferPause = 700 / speed;
    const betweenStepsPause = 24 / speed;
    const animationBudget = Math.max(
      1200,
      targetRouteDuration
        - initialPause
        - transferCount * transferPause
        - transitionPairs.length * betweenStepsPause
    );
    const rideDuration = Math.max(110, Math.min(800, animationBudget / rideCount));

    if (!keepPrevious) setCompleted([]);

    setActive({ route, index, color });
    setTrace([coords[0]]);
    setMarker({ ...coords[0], color });
    setTransfer(null);
    setVisitedStep(0);

    if (fit) fitRoute(route);

    onPlaybackState?.({
      routeNumber,
      totalRoutes,
      stationIndex: 1,
      stationCount: coords.length,
      station: coords[0].station,
      color,
      phase: 'ride',
    });

    await wait(initialPause);

    for (let i = 1; i < coords.length; i += 1) {
      if (cancelRef.current !== runId) return false;

      const a = coords[i - 1];
      const b = coords[i];
      const isTransfer = a.station === b.station && lineFamily(a.line) !== lineFamily(b.line);

      if (isTransfer) {
        setMarker({ ...b, color });
        setTransfer({
          station: a.station,
          from: lineFamily(a.line),
          to: lineFamily(b.line),
        });

        onPlaybackState?.({
          routeNumber,
          totalRoutes,
          stationIndex: i + 1,
          stationCount: coords.length,
          station: b.station,
          color,
          phase: 'transfer',
          fromLine: lineFamily(a.line),
          toLine: lineFamily(b.line),
        });

        await wait(transferPause);

        if (cancelRef.current !== runId) return false;

        setTransfer(null);
        setTrace(prev => [...prev, b]);
        setVisitedStep(i);
      } else {
        onPlaybackState?.({
          routeNumber,
          totalRoutes,
          stationIndex: i + 1,
          stationCount: coords.length,
          station: b.station,
          color,
          phase: 'ride',
        });

        // Append a temporary endpoint. move() replaces that endpoint
        // frame-by-frame so the route appears to be drawn forward.
        setTrace(prev => [...prev, b]);

        const ok = await move(
          a,
          b,
          color,
          runId,
          rideDuration
        );

        if (!ok) return false;
        setVisitedStep(i);
      }

      await wait(betweenStepsPause);
    }

    setCompleted(prev => [
      ...prev.filter(item => item.index !== index),
      { route, index, color },
    ]);

    setMarker(null);
    setTransfer(null);
    setVisitedStep(coords.length - 1);

    onPlaybackState?.({
      routeNumber,
      totalRoutes,
      stationIndex: coords.length,
      stationCount: coords.length,
      station: coords.at(-1)?.station,
      color,
      phase: 'done',
      done: true,
    });

    return true;
  }

  function showFinalComparison() {
    setActive(null);
    setTrace([]);
    setMarker(null);
    setTransfer(null);
    setVisitedStep(-1);
    fitAll(routes);
  }

  useImperativeHandle(ref, () => ({
    playRoute,
    reset,
    stop,
    fitAll,
    fitRoute,
    showFinalComparison,
  }));

  if (!network) {
    return <div className="map-loading">Loading Taipei Metro network…</div>;
  }

  return (
    <div className={`map-wrap ${playing ? 'is-playing' : ''}`}>
      <div className="map-surface">
      <MapContainer
        center={[25.045, 121.54]}
        zoom={11.5}
        minZoom={compact ? 9 : 10.5}
        maxZoom={16}
        zoomSnap={0.25}
        zoomDelta={0.5}
        wheelPxPerZoomLevel={120}
        maxBounds={METRO_MAX_BOUNDS}
        maxBoundsViscosity={1.0}
        scrollWheelZoom
        dragging
        touchZoom
        doubleClickZoom
        className="map"
      >
        <MapSizeObserver compact={compact} />
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          eventHandlers={{
            tileerror: () => setTileError(true),
            load: () => setTileError(false),
          }}
        />

        {/* Full Taipei Metro network: deliberately muted. */}
        {(network.edges || []).map(edge => (
          <Polyline
            key={edge.id}
            positions={edge.positions}
            pathOptions={{
              color: colorForLine(edge.line),
              weight: 3.2,
              opacity: 0.16,
            }}
            interactive={false}
          />
        ))}

        {/* All Pareto alternatives remain faintly visible as context. */}
        {routes.map((route, index) => {
          const coords = routeCoords(route);
          if (coords.length < 2) return null;

          return (
            <Polyline
              key={`overview-${index}`}
              positions={coords.map(p => [p.lat, p.lon])}
              pathOptions={{
                color: colors[index] || '#64748b',
                weight: active?.index === index ? 3.2 : 2.4,
                opacity: finalComparison
                  ? 0.04
                  : active?.index === index
                    ? 0.16
                    : completedIndexes.has(index)
                      ? 0.08
                      : 0.10,
                dashArray: completedIndexes.has(index) ? undefined : '4 9',
                lineCap: 'round',
                lineJoin: 'round',
              }}
              interactive={false}
            />
          );
        })}

        {/* Routes already shown in Play All remain as a visual memory. */}
        {completed.map(item => (
          <Polyline
            key={`done-${item.index}`}
            positions={routeCoords(item.route).map(p => [p.lat, p.lon])}
            pathOptions={{
              color: item.color,
              weight: finalComparison ? 4.0 : 3.6,
              opacity: finalComparison ? 0.72 : active?.index === item.index ? 0.28 : 0.38,
              lineCap: 'round',
              lineJoin: 'round',
            }}
            interactive={false}
          />
        ))}

        {/* Full active route guide below the animated trace. */}
        {active && !finalComparison && (
          <Polyline
            positions={routeCoords(active.route).map(p => [p.lat, p.lon])}
            pathOptions={{
              color: active.color,
              weight: 4.4,
              opacity: 0.16,
              dashArray: '2 10',
              lineCap: 'round',
              lineJoin: 'round',
            }}
            interactive={false}
          />
        )}

        {/* Animated route trace. */}
        {active && !finalComparison && trace.length > 1 && (
          <>
            <Polyline
              positions={trace.map(p => [p.lat, p.lon])}
              pathOptions={{
                color: '#ffffff',
                weight: 7.4,
                opacity: 0.92,
                lineCap: 'round',
                lineJoin: 'round',
              }}
              interactive={false}
            />
            <Polyline
              positions={trace.map(p => [p.lat, p.lon])}
              pathOptions={{
                color: active.color,
                weight: 4.6,
                opacity: 0.98,
                lineCap: 'round',
                lineJoin: 'round',
              }}
              interactive={false}
            />
          </>
        )}

        {/* Metro station nodes. */}
        {(network.stations || []).map(station => {
          const isOrigin = station.id === origin;
          const isDestination = station.id === destination;
          const familyCount = new Set((station.lines || []).map(lineFamily).filter(Boolean)).size;
          const isNetworkTransfer = familyCount >= 2;
          const isParetoTransfer = paretoTransferStations.has(station.id);
          const radius = isOrigin || isDestination ? 8 : isParetoTransfer ? 5.4 : isNetworkTransfer ? 4.3 : compact ? 4.2 : 3.4;

          return (
            <React.Fragment key={station.id}>
              <CircleMarker
                center={[station.lat, station.lon]}
                radius={radius}
                pathOptions={{
                  color: isOrigin
                    ? '#0f172a'
                    : isDestination
                      ? '#ffffff'
                      : isParetoTransfer
                        ? '#334155'
                        : '#64748b',
                  weight: isOrigin || isDestination ? 3 : isParetoTransfer ? 2.3 : isNetworkTransfer ? 1.8 : 1.35,
                  fillColor: isDestination ? '#0f172a' : '#ffffff',
                  fillOpacity: 1,
                  opacity: isOrigin || isDestination || isParetoTransfer ? 1 : 0.72,
                }}
                eventHandlers={{
                  click: () => onStationClick?.(station.id),
                }}
              >
                <Tooltip
                  direction="top"
                  permanent={isOrigin || isDestination || (isParetoTransfer && !playing && !compact)}
                  className={
                    isOrigin || isDestination
                      ? 'od-tooltip'
                      : isParetoTransfer
                        ? 'transfer-tooltip'
                        : ''
                  }
                  offset={[0, -6]}
                >
                  {isOrigin
                    ? `O · ${station.id}`
                    : isDestination
                      ? `D · ${station.id}`
                      : station.id}
                </Tooltip>
              </CircleMarker>

              {isParetoTransfer && !isOrigin && !isDestination && (
                <CircleMarker
                  center={[station.lat, station.lon]}
                  radius={2.0}
                  pathOptions={{
                    color: '#334155',
                    weight: 1,
                    fillColor: '#ffffff',
                    fillOpacity: 1,
                    opacity: 1,
                  }}
                  interactive={false}
                />
              )}
            </React.Fragment>
          );
        })}

        {/* Station markers + permanent labels for the currently emphasized route.
            Origin / destination already have their own O / D labels, so they are
            intentionally not duplicated here. */}
        {active && routeLabelPoints
          .filter(point => point.station !== origin && point.station !== destination)
          .map((point, labelIndex) => (
            <CircleMarker
              key={`route-station-${active.index}-${point.station}`}
              center={[point.lat, point.lon]}
              radius={point.isTransfer ? 7.0 : point.visited ? 6.2 : 5.2}
              pathOptions={{
                color: point.isTransfer ? '#0f172a' : point.visited ? '#ffffff' : active.color,
                weight: point.isTransfer ? 2.8 : point.visited ? 2.3 : 1.8,
                fillColor: point.visited ? active.color : '#ffffff',
                fillOpacity: point.visited ? 1 : 0.88,
                opacity: point.visited ? 1 : 0.72,
              }}
              interactive={false}
            >
              <Tooltip
                permanent={!compact || point.station === currentStation || (point.isTransfer && routeLabelPoints.filter(p => p.isTransfer).slice(0, 3).some(p => p.station === point.station))}
                direction={labelIndex % 2 === 0 ? 'top' : 'bottom'}
                offset={[0, labelIndex % 2 === 0 ? -5 : 5]}
                className={`route-station-tooltip ${point.visited ? 'visited' : 'upcoming'}`}
              >
                {point.station}
              </Tooltip>
            </CircleMarker>
          ))}

        {/* Animated vehicle / route cursor. */}
        {marker && (
          <>
            <CircleMarker
              center={[marker.lat, marker.lon]}
              radius={transfer ? 22 : 16}
              pathOptions={{
                color: marker.color,
                weight: transfer ? 3 : 2,
                fillColor: marker.color,
                fillOpacity: transfer ? 0.10 : 0.08,
                opacity: transfer ? 0.68 : 0.42,
                className: transfer ? 'leaflet-transfer-ring' : 'leaflet-moving-ring',
              }}
              interactive={false}
            />

            {transfer && (
              <CircleMarker
                center={[marker.lat, marker.lon]}
                radius={13}
                pathOptions={{
                  color: '#ffffff',
                  weight: 2,
                  fillColor: marker.color,
                  fillOpacity: 0.22,
                  opacity: 0.85,
                  className: 'leaflet-transfer-ring-2',
                }}
                interactive={false}
              />
            )}

            <CircleMarker
              center={[marker.lat, marker.lon]}
              radius={7.2}
              pathOptions={{
                color: '#ffffff',
                weight: 3.5,
                fillColor: marker.color,
                fillOpacity: 1,
                opacity: 1,
              }}
              interactive={false}
            />
          </>
        )}

        {!!fitCoords.length && <FitBounds coords={fitCoords} token={fitToken} playing={playing} />}
      </MapContainer>
      </div>
      <div className="map-notes">
      {tileError && (
        <div className="offline-map-warning" role="status">
          底圖目前無法載入；捷運路網與 Pareto 路徑仍可正常展示
        </div>
      )}

      {finalComparison && (
        <div className="final-map-label">ALL PARETO ROUTES</div>
      )}

      <div className="map-legend">
        <span><i className="legend-active" /> active route</span>
        <span><i className="legend-complete" /> completed</span>
        <span><i className="legend-network" /> metro network</span>
      </div>

      <p className="map-tip">
        {playing
          ? '播放中：目前路徑加亮；轉乘站以 ◎ 與脈衝提示'
          : finalComparison
            ? '比較完成：所有 Pareto alternatives 同時保留於地圖'
            : '地圖已限制在雙北捷運範圍；點兩個車站即可選 OD'}
      </p>
      </div>
    </div>
  );
});

export default MetroMap;
