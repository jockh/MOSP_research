import React from 'react';
import { Play, RotateCcw } from 'lucide-react';

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

export default function RoutePanel({
  routes,
  colors,
  active,
  playing,
  onPlay,
  onPlayAll,
  onReset,
  finalComparison = false,
}) {
  return (
    <section className="panel route-panel">
      <div className="panel-head">
        <div>
          <div className="eyebrow">PARETO SOLUTIONS</div>
          <h2>{routes.length ? `${routes.length} 條路徑` : '尚未搜尋'}</h2>
        </div>

        <button className="icon" onClick={onReset} title="Reset animation" aria-label="重設動畫">
          <RotateCcw size={16} />
        </button>
      </div>

      {routes.length > 0 && (
        <button className="play-all" onClick={onPlayAll} disabled={playing}>
          <Play size={16} fill="currentColor" />
          {playing ? '依序播放中…' : '依序播放全部 R1 → Rn'}
        </button>
      )}

      <div className="routes">
        {routes.map((route, index) => (
          <article
            key={index}
            className={`route-card ${active === index ? 'active' : ''} ${finalComparison ? 'shown' : ''}`}
            style={{ '--c': colors[index] }}
          >
            <div className="route-top">
              <div className="rname">
                <span style={{ background: colors[index] }} />
                R{index + 1}
                {active === index && playing && <em>NOW</em>}
              </div>

              <button type="button" aria-label={`播放路徑 R${index + 1}`} onClick={() => onPlay(index)} disabled={playing}>
                <Play size={13} fill="currentColor" />播放
              </button>
            </div>

            <div className="metrics">
              <Metric k="旅行時間" v={`${route.travel_time_minutes.toFixed(2)} 分`} />
              <Metric k="轉乘" v={`${route.transfers} 次`} />
              <Metric k="步行" v={`${route.walking_minutes.toFixed(0)} 分`} />
            </div>

            <div className="line-seq">
              {lineSeq(route.path).map((line, segmentIndex) => (
                <span
                  className={`line-chip ${line === 'Y' ? 'dark' : ''}`}
                  key={`${line}-${segmentIndex}`}
                  style={{ background: LINE_COLORS[line] || '#64748b' }}
                >
                  {line}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Metric({ k, v }) {
  return (
    <div>
      <span>{k}</span>
      <strong>{v}</strong>
    </div>
  );
}

function lineSeq(path = []) {
  const lines = [];

  for (const point of path) {
    const line = lineFamily(point.line);
    if (line && lines.at(-1) !== line) {
      lines.push(line);
    }
  }

  return lines;
}
