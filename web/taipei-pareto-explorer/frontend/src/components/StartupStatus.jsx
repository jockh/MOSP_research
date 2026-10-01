import React from 'react';

export default function StartupStatus({ phase, attempt, onRetry }) {
  const failed = phase === 'error';
  return (
    <section className="startup-card" role={failed ? 'alert' : 'status'} aria-live="polite" aria-atomic="true">
      {!failed && <span className="startup-spinner" aria-hidden="true" />}
      <div className="startup-copy">
        <h2>{failed ? '暫時無法連線到伺服器' : '正在載入臺北捷運 Pareto 路徑資料…'}</h2>
        <p>{failed
          ? '已等待約 3 分鐘。請檢查網路連線，再試一次；不需要重新整理頁面。'
          : '首次開啟時伺服器可能需要一些時間啟動，請稍候。'}</p>
        {!failed && <p className="startup-detail">{phase === 'loading'
          ? '伺服器已連線，正在載入車站與 Pareto 路徑…'
          : attempt > 1 || phase === 'retrying'
            ? `目前仍在嘗試連線（第 ${attempt} 次）…將自動重試。`
            : '正在連線到伺服器…'}</p>}
        {failed && <button type="button" className="search startup-retry" onClick={onRetry}>重新嘗試</button>}
      </div>
    </section>
  );
}
