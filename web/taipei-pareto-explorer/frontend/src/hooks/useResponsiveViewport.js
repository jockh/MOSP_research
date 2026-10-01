import { useEffect, useState } from 'react';

const COMPACT_MAP = '(max-width: 768px), (max-width: 1024px) and (max-height: 600px)';

export function useCompactMap() {
  const [compact, setCompact] = useState(() => window.matchMedia(COMPACT_MAP).matches);
  useEffect(() => {
    const query = window.matchMedia(COMPACT_MAP);
    const update = () => setCompact(query.matches);
    update();
    if (query.addEventListener) query.addEventListener('change', update);
    else query.addListener(update);
    return () => {
      if (query.removeEventListener) query.removeEventListener('change', update);
      else query.removeListener(update);
    };
  }, []);
  return compact;
}

// Older Safari has no dvh. Keep its fallback tied to the visible viewport,
// while leaving page pinch zoom and native form controls in charge of zooming.
export function useViewportHeightFallback() {
  useEffect(() => {
    if (window.CSS?.supports('height', '100dvh')) return undefined;
    const root = document.documentElement;
    const previous = root.style.getPropertyValue('--viewport-height');
    const viewport = window.visualViewport;
    let frame;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        if (viewport && Math.abs(viewport.scale - 1) > 0.01) return;
        const height = viewport?.height || window.innerHeight;
        if (height > 0) root.style.setProperty('--viewport-height', `${height}px`);
      });
    };
    update();
    window.addEventListener('resize', update);
    window.addEventListener('orientationchange', update);
    window.addEventListener('pageshow', update);
    viewport?.addEventListener('resize', update);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('resize', update);
      window.removeEventListener('orientationchange', update);
      window.removeEventListener('pageshow', update);
      viewport?.removeEventListener('resize', update);
      if (previous) root.style.setProperty('--viewport-height', previous);
      else root.style.removeProperty('--viewport-height');
    };
  }, []);
}
