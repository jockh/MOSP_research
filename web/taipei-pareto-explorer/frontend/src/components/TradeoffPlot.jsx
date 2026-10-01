import React from 'react';

export default function TradeoffPlot({
  routes,
  colors,
  active,
  playing,
  onPlay,
  finalComparison = false,
}) {
  if (!routes.length) {
    return (
      <section className="panel">
        <div className="eyebrow">TRADE-OFF VIEW</div>
        <h2>Pareto cost space</h2>
        <p className="muted">搜尋後顯示旅行時間與轉乘步行取捨。</p>
      </section>
    );
  }

  const W = 360;
  const H = 235;
  const P = { l: 48, r: 20, t: 22, b: 42 };

  let xs = routes.map(r => r.travel_time_minutes);
  let ys = routes.map(r => r.walking_minutes);

  let xmin = Math.min(...xs);
  let xmax = Math.max(...xs);
  let ymin = Math.min(...ys);
  let ymax = Math.max(...ys);

  if (xmin === xmax) {
    xmin -= 1;
    xmax += 1;
  }

  if (ymin === ymax) {
    ymin -= 1;
    ymax += 1;
  }

  const xPad = Math.max(0.35, (xmax - xmin) * 0.08);
  const yPad = Math.max(0.25, (ymax - ymin) * 0.12);

  xmin -= xPad;
  xmax += xPad;
  ymin = Math.max(0, ymin - yPad);
  ymax += yPad;

  const sx = x => P.l + ((x - xmin) / (xmax - xmin)) * (W - P.l - P.r);
  const sy = y => H - P.b - ((y - ymin) / (ymax - ymin)) * (H - P.t - P.b);

  const sorted = routes
    .map((route, index) => ({ ...route, index }))
    .sort((a, b) => a.travel_time_minutes - b.travel_time_minutes);

  const xTicks = [xmin, (xmin + xmax) / 2, xmax];
  const yTicks = [ymin, (ymin + ymax) / 2, ymax];

  return (
    <section className="panel tradeoff-panel">
      <div className="eyebrow">TRADE-OFF VIEW</div>

      <div className="plot-title">
        <h2>Pareto cost space</h2>
        <span>圓點大小＝轉乘次數</span>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="plot" aria-label="Pareto 旅行時間與轉乘步行取捨圖">
        {xTicks.map((tick, index) => (
          <g key={`x-${index}`}>
            <line
              className="gridline"
              x1={sx(tick)}
              y1={P.t}
              x2={sx(tick)}
              y2={H - P.b}
            />
            <text className="ticklabel" x={sx(tick)} y={H - P.b + 15} textAnchor="middle">
              {tick.toFixed(1)}
            </text>
          </g>
        ))}

        {yTicks.map((tick, index) => (
          <g key={`y-${index}`}>
            <line
              className="gridline"
              x1={P.l}
              y1={sy(tick)}
              x2={W - P.r}
              y2={sy(tick)}
            />
            <text className="ticklabel" x={P.l - 7} y={sy(tick) + 3} textAnchor="end">
              {tick.toFixed(1)}
            </text>
          </g>
        ))}

        <line className="axis" x1={P.l} y1={H - P.b} x2={W - P.r} y2={H - P.b} />
        <line className="axis" x1={P.l} y1={P.t} x2={P.l} y2={H - P.b} />

        <polyline
          fill="none"
          points={sorted
            .map(route => `${sx(route.travel_time_minutes)},${sy(route.walking_minutes)}`)
            .join(' ')}
          className="frontier"
        />

        {routes.map((route, index) => {
          const x = sx(route.travel_time_minutes);
          const y = sy(route.walking_minutes);
          const radius = 5 + route.transfers * 1.15;
          const isActive = active === index;

          return (
            <g
              key={index}
              className={`dot ${isActive ? 'active' : ''} ${playing ? 'disabled' : ''}`}
              role="button"
              tabIndex={playing ? -1 : 0}
              aria-disabled={playing}
              aria-pressed={isActive}
              aria-label={`播放 R${index + 1}：${route.travel_time_minutes.toFixed(2)} 分，${route.transfers} 次轉乘，步行 ${route.walking_minutes.toFixed(0)} 分`}
              onKeyDown={event => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  if (!playing) onPlay(index);
                }
              }}
              onClick={() => !playing && onPlay(index)}
            >
              <circle className="plot-hit-area" cx={x} cy={y} r="1" fill="transparent" stroke="transparent" strokeWidth="44" vectorEffect="non-scaling-stroke" />
              <title>
                {`R${index + 1}: ${route.travel_time_minutes.toFixed(2)} min, ${route.transfers} transfers, ${route.walking_minutes.toFixed(0)} min walk`}
              </title>

              {isActive && !finalComparison && (
                <circle
                  className="plot-pulse"
                  cx={x}
                  cy={y}
                  r={radius + 8}
                  fill="none"
                  stroke={colors[index]}
                  strokeWidth="2"
                />
              )}

              {finalComparison && (
                <circle
                  className="plot-final-ring"
                  cx={x}
                  cy={y}
                  r={radius + 5}
                  fill="none"
                  stroke={colors[index]}
                  strokeWidth="1.8"
                />
              )}

              <circle
                cx={x}
                cy={y}
                r={radius}
                fill={colors[index]}
                stroke="#ffffff"
                strokeWidth="2.5"
              />

              <text x={x + 10} y={y - 9}>R{index + 1}</text>
            </g>
          );
        })}

        <text
          className="axislabel"
          x={(P.l + W - P.r) / 2}
          y={H - 5}
          textAnchor="middle"
        >
          旅行時間（分鐘）
        </text>

        <text
          className="axislabel"
          x="12"
          y={(P.t + H - P.b) / 2}
          textAnchor="middle"
          transform={`rotate(-90 12 ${(P.t + H - P.b) / 2})`}
        >
          轉乘步行（分鐘）
        </text>
      </svg>
      <div className="plot-route-buttons" aria-label="Pareto chart routes">
        {routes.map((route, index) => (
          <button
            type="button"
            key={index}
            className="plot-route-button"
            style={{ '--c': colors[index] }}
            aria-pressed={active === index}
            aria-label={`播放圖表路徑 R${index + 1}`}
            disabled={playing}
            onClick={() => onPlay(index)}
          >
            <i aria-hidden="true" /><strong>R{index + 1}</strong>
            <span>{route.travel_time_minutes.toFixed(2)} 分 · {route.transfers} 次轉乘 · 步行 {route.walking_minutes.toFixed(0)} 分</span>
          </button>
        ))}
      </div>
      <p className="plot-hint">點選圓點或路徑按鈕播放；地圖、路徑卡與圖表同步加亮。</p>
    </section>
  );
}
