import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, Play, Search, Square } from 'lucide-react';
import { getHealth, getNetwork, getRoutes, getStations } from './api.js';
import MetroMap from './components/MetroMap.jsx';
import RoutePanel from './components/RoutePanel.jsx';
import TradeoffPlot from './components/TradeoffPlot.jsx';
import { useViewportHeightFallback } from './hooks/useResponsiveViewport.js';

const COLORS = ['#ef4444', '#2563eb', '#10b981', '#8b5cf6', '#f97316', '#ec4899', '#06b6d4', '#84cc16'];
const SPEEDS = [1, 1.5, 2];

const LINE_ORDER = ['BR', 'R', 'G', 'O', 'BL', 'Y'];
const LINE_NAMES = {
  BR: '文湖線',
  R: '淡水信義線',
  G: '松山新店線',
  O: '中和新蘆線',
  BL: '板南線',
  Y: '環狀線',
};
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

export default function App() {
  const mapRef = useRef(null);
  useViewportHeightFallback();
  const [health, setHealth] = useState(null);
  const [stations, setStations] = useState([]);
  const [network, setNetwork] = useState(null);

  // OD is selected in two stages: line first, then station.
  const [originLine, setOriginLine] = useState('BR');
  const [destinationLine, setDestinationLine] = useState('Y');
  const [origin, setOrigin] = useState('東湖站');
  const [destination, setDestination] = useState('中原站');

  const [routes, setRoutes] = useState([]);
  const [active, setActive] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [playback, setPlayback] = useState(null);
  const [speed, setSpeed] = useState(2);
  const [finalComparison, setFinalComparison] = useState(false);
  const [error, setError] = useState('');

  const colors = useMemo(
    () => routes.map((_, i) => COLORS[i % COLORS.length]),
    [routes]
  );

  const stationsByLine = useMemo(() => {
    const grouped = {};

    (network?.stations || []).forEach(station => {
      const families = [...new Set((station.lines || []).map(lineFamily).filter(Boolean))];
      families.forEach(line => {
        if (!grouped[line]) grouped[line] = [];
        grouped[line].push(station.id);
      });
    });

    Object.keys(grouped).forEach(line => {
      grouped[line] = [...new Set(grouped[line])].sort((a, b) => a.localeCompare(b, 'zh-Hant'));
    });

    return grouped;
  }, [network]);

  const stationLineLookup = useMemo(() => {
    const lookup = new Map();
    (network?.stations || []).forEach(station => {
      lookup.set(
        station.id,
        [...new Set((station.lines || []).map(lineFamily).filter(Boolean))]
      );
    });
    return lookup;
  }, [network]);

  const availableLines = useMemo(() => {
    const discovered = Object.keys(stationsByLine);
    const ordered = LINE_ORDER.filter(line => discovered.includes(line));
    const extra = discovered.filter(line => !LINE_ORDER.includes(line)).sort();
    return [...ordered, ...extra];
  }, [stationsByLine]);

  const originStations = originLine ? (stationsByLine[originLine] || []) : [];
  const destinationStations = destinationLine ? (stationsByLine[destinationLine] || []) : [];

  useEffect(() => {
    (async () => {
      try {
        const h = await getHealth();
        setHealth(h);
        if (!h.ok) throw new Error(h.station_error || 'Backend data not ready');
        const [s, n] = await Promise.all([getStations(), getNetwork()]);
        setStations(s.stations);
        setNetwork(n);
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  const clearRouteDisplay = useCallback(() => {
    setRoutes([]);
    setActive(null);
    setPlayback(null);
    setFinalComparison(false);
    setError('');
    mapRef.current?.reset();
  }, []);

  const search = useCallback(async () => {
    if (!origin || !destination || origin === destination) return;
    try {
      setError('');
      mapRef.current?.reset();
      setActive(null);
      setPlayback(null);
      setFinalComparison(false);
      const result = await getRoutes(origin, destination);
      setRoutes(result.routes);
      if (result.missing_coordinate_stations?.length) {
        setError('缺少座標：' + result.missing_coordinate_stations.join('、'));
      }
    } catch (e) {
      setRoutes([]);
      setError(e.message);
    }
  }, [origin, destination]);

  // Search automatically after both station selections are complete.
  useEffect(() => {
    if (!stations.length || !origin || !destination || origin === destination) return;
    const timer = setTimeout(() => search(), 60);
    return () => clearTimeout(timer);
  }, [stations.length, origin, destination, search]);

  useEffect(() => {
    if (!routes.length) return;
    const timer = setTimeout(() => mapRef.current?.fitAll(routes), 120);
    return () => clearTimeout(timer);
  }, [routes]);

  const chooseLineForStation = useCallback((station, preferred = '') => {
    const lines = stationLineLookup.get(station) || [];
    if (preferred && lines.includes(preferred)) return preferred;
    return LINE_ORDER.find(line => lines.includes(line)) || lines[0] || '';
  }, [stationLineLookup]);

  const handleOriginLineChange = useCallback(event => {
    setOriginLine(event.target.value);
    setOrigin('');
    clearRouteDisplay();
  }, [clearRouteDisplay]);

  const handleDestinationLineChange = useCallback(event => {
    setDestinationLine(event.target.value);
    setDestination('');
    clearRouteDisplay();
  }, [clearRouteDisplay]);

  const handleOriginStationChange = useCallback(event => {
    setOrigin(event.target.value);
    clearRouteDisplay();
  }, [clearRouteDisplay]);

  const handleDestinationStationChange = useCallback(event => {
    setDestination(event.target.value);
    clearRouteDisplay();
  }, [clearRouteDisplay]);

  const playOne = useCallback(async index => {
    if (playing || !routes[index]) return;
    setPlaying(true);
    setActive(index);
    setFinalComparison(false);
    try {
      await mapRef.current?.playRoute(routes[index], index, colors[index], {
        keepPrevious: false,
        routeNumber: index + 1,
        totalRoutes: routes.length,
        speed,
        fit: true,
      });
    } finally {
      setPlaying(false);
      setPlayback(null);
    }
  }, [routes, colors, playing, speed]);

  const playAll = useCallback(async () => {
    if (playing || !routes.length) return;

    setPlaying(true);
    setPlayback(null);
    setFinalComparison(false);
    mapRef.current?.reset();
    mapRef.current?.fitAll(routes);

    let finishedAll = true;

    try {
      await new Promise(resolve => setTimeout(resolve, 380));

      for (let i = 0; i < routes.length; i += 1) {
        setActive(i);

        const ok = await mapRef.current?.playRoute(routes[i], i, colors[i], {
          keepPrevious: true,
          routeNumber: i + 1,
          totalRoutes: routes.length,
          speed,
          fit: false,
        });

        if (ok === false) {
          finishedAll = false;
          break;
        }

        await new Promise(resolve => setTimeout(resolve, 260 / speed));
      }
    } finally {
      setPlaying(false);
      setPlayback(null);
      setActive(null);

      if (finishedAll) {
        setFinalComparison(true);
        mapRef.current?.showFinalComparison?.();
      } else {
        setFinalComparison(false);
      }
    }
  }, [routes, colors, playing, speed]);

  const stopPlayback = useCallback(() => {
    mapRef.current?.stop();
    setPlaying(false);
    setPlayback(null);
    setActive(null);
    setFinalComparison(false);
  }, []);

  const stationClick = useCallback(station => {
    const lines = stationLineLookup.get(station) || [];

    // If a complete OD already exists, clicking the map starts a new OD from that station.
    if (origin && destination) {
      setOriginLine(chooseLineForStation(station, originLine));
      setOrigin(station);
      setDestinationLine('');
      setDestination('');
      clearRouteDisplay();
      return;
    }

    // Origin exists, so the next map click becomes destination.
    if (origin && station !== origin) {
      const preferred = lines.includes(destinationLine) ? destinationLine : '';
      setDestinationLine(chooseLineForStation(station, preferred));
      setDestination(station);
      clearRouteDisplay();
      return;
    }

    if (!origin) {
      setOriginLine(chooseLineForStation(station, originLine));
      setOrigin(station);
      clearRouteDisplay();
    }
  }, [origin, destination, originLine, destinationLine, stationLineLookup, chooseLineForStation, clearRouteDisplay]);

  const progress = playback
    ? Math.round((playback.stationIndex / Math.max(1, playback.stationCount)) * 100)
    : 0;

  return (
    <div className="app">
      <header>
        <div>
          <div className="eyebrow blue">NTU CIVIL · TRANSPORTATION · MOSP</div>
          <h1>Taipei Pareto Route Explorer</h1>
          <p>旅行時間 × 轉乘次數 × 轉乘步行時間</p>
        </div>
        <div className={`status ${health?.ok ? 'ok' : ''}`}>
          <i />
          {health?.ok ? 'All-OD Pareto data ready' : 'Data not ready'}
        </div>
      </header>

      <div className="controls od-controls">
        <div className="od-block">
          <div className="od-block-title">
            <span>Origin</span>
            {originLine && (
              <b
                className={`selected-line-badge ${originLine === 'Y' ? 'dark' : ''}`}
                style={{ '--line-color': LINE_COLORS[originLine] || '#64748b' }}
              >
                {originLine}
              </b>
            )}
          </div>

          <div className="od-block-fields">
            <label className="line-field">
              <span>1 · Line</span>
              <select aria-label="Origin line" value={originLine} onChange={handleOriginLineChange} disabled={playing}>
                <option value="">選路線</option>
                {availableLines.map(line => (
                  <option key={line} value={line}>
                    {line} · {LINE_NAMES[line] || line}
                  </option>
                ))}
              </select>
            </label>

            <label className="station-field">
              <span>2 · Station</span>
              <select
                aria-label="Origin station"
                value={origin}
                onChange={handleOriginStationChange}
                disabled={!originLine || playing}
              >
                <option value="">{originLine ? '選起點車站' : '請先選路線'}</option>
                {originStations.map(station => (
                  <option key={station} value={station}>
                    {station}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <ArrowRight className="arrow od-arrow" size={20} />

        <div className="od-block">
          <div className="od-block-title">
            <span>Destination</span>
            {destinationLine && (
              <b
                className={`selected-line-badge ${destinationLine === 'Y' ? 'dark' : ''}`}
                style={{ '--line-color': LINE_COLORS[destinationLine] || '#64748b' }}
              >
                {destinationLine}
              </b>
            )}
          </div>

          <div className="od-block-fields">
            <label className="line-field">
              <span>1 · Line</span>
              <select aria-label="Destination line" value={destinationLine} onChange={handleDestinationLineChange} disabled={playing}>
                <option value="">選路線</option>
                {availableLines.map(line => (
                  <option key={line} value={line}>
                    {line} · {LINE_NAMES[line] || line}
                  </option>
                ))}
              </select>
            </label>

            <label className="station-field">
              <span>2 · Station</span>
              <select
                aria-label="Destination station"
                value={destination}
                onChange={handleDestinationStationChange}
                disabled={!destinationLine || playing}
              >
                <option value="">{destinationLine ? '選終點車站' : '請先選路線'}</option>
                {destinationStations.map(station => (
                  <option key={station} value={station} disabled={station === origin}>
                    {station}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <button
          className="search"
          onClick={search}
          disabled={playing || !origin || !destination || origin === destination}
        >
          <Search size={16} /> Find Pareto Routes
        </button>

      </div>

      {error && <div className="error" role="alert">{error}</div>}

      <main aria-label="Pareto route results">
        <section className="mapcol">
          <div className="maphead">
            <div>
              <div className="eyebrow">NETWORK VIEW</div>
              <h2>{origin || 'Origin'} <span>→</span> {destination || 'Destination'}</h2>
            </div>
            {routes.length > 0 && <b>{routes.length} Pareto solutions</b>}
          </div>

          <div className="map-stage">
            <MetroMap
              ref={mapRef}
              network={network}
              routes={routes}
              colors={colors}
              playing={playing}
              origin={origin}
              destination={destination}
              onStationClick={stationClick}
              onPlaybackState={setPlayback}
              finalComparison={finalComparison}
            />


          </div>
          {routes.length > 0 && (
            <div className="animation-controls" aria-label="Animation controls">
              {playing ? (
                <button type="button" className="stop" onClick={stopPlayback}>
                  <Square size={16} fill="currentColor" /> Stop
                </button>
              ) : (
                <button type="button" className="playtop" onClick={playAll}>
                  <Play size={16} fill="currentColor" /> Play All
                </button>
              )}
              <div className="speed-control" role="group" aria-label="animation speed">
                <span>Speed</span>
                {SPEEDS.map(value => (
                  <button
                    type="button"
                    key={value}
                    className={speed === value ? 'selected' : ''}
                    aria-pressed={speed === value}
                    onClick={() => setSpeed(value)}
                    disabled={playing}
                  >
                    {value}×
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="map-feedback">
            {finalComparison && !playback && (
              <div className="comparison-hud">
                <strong>All Pareto routes shown</strong>
                <span>{routes.length} non-dominated alternatives · compare travel time, transfers and walking</span>
              </div>
            )}

            {playback && (
              <div className="playback-hud" style={{ '--route-color': playback.color }}>
                <div className="playback-topline">
                  <strong>R{playback.routeNumber}</strong>
                  <span>{playback.routeNumber} / {playback.totalRoutes}</span>
                </div>

                <div className="playback-phase">
                  {playback.phase === 'transfer' ? 'TRANSFER' : playback.done ? 'ROUTE COMPLETE' : 'RIDING'}
                </div>

                <div className="playback-station">{playback.station}</div>

                {playback.phase === 'transfer' && playback.fromLine && playback.toLine && (
                  <div className="playback-transfer">
                    {lineFamily(playback.fromLine)} <span>→</span> {lineFamily(playback.toLine)}
                  </div>
                )}

                <div className="playback-meta">
                  station {playback.stationIndex} / {playback.stationCount}
                </div>

                <div className="progress-track" role="progressbar" aria-label="路徑播放進度" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}>
                  <div className="progress-fill" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}
          </div>
        </section>

        <aside>
          <RoutePanel
            routes={routes}
            colors={colors}
            active={active}
            playing={playing}
            onPlay={playOne}
            onPlayAll={playAll}
            finalComparison={finalComparison}
            onReset={() => {
              mapRef.current?.reset();
              mapRef.current?.fitAll(routes);
              setActive(null);
              setPlayback(null);
              setFinalComparison(false);
            }}
          />

          <TradeoffPlot
            routes={routes}
            colors={colors}
            active={active}
            playing={playing}
            onPlay={playOne}
            finalComparison={finalComparison}
          />
        </aside>
      </main>

      <footer>
        <span>Pareto-optimal ≠ universally preferred.</span>
        <span>Non-dominated alternatives before passenger preference is specified.</span>
      </footer>
    </div>
  );
}
