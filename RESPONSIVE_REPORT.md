# Responsive implementation and verification

The single frontend now has a mobile-first layout: OD controls → map → playback controls/status → route cards → tradeoff plot. CSS adapts at 480, 768 and 1024 pixels. Desktop retains a map/sidebar layout; tablet uses a full-width map and two-column panels; mobile uses normal vertical page scrolling without a nested route-list scroll region.

## iOS Safari requirements implemented

- `viewport-fit=cover`; safe-area insets on header, content, controls and footer.
- `100vh` fallback, dynamic `100dvh` in supported browsers, and an older-browser `visualViewport` resize/orientation fallback. The fallback ignores pinch-scale changes and removes listeners on cleanup.
- Full-width native select controls with 16px text and 48px height. Page zoom is not disabled.
- Buttons/zoom controls have at least 44px touch targets. Native Leaflet pan, touch zoom and double-click zoom remain enabled. Generic page scrolling remains available outside the map.
- `ResizeObserver`, orientation/window/visualViewport events invalidate Leaflet size; route fitting adapts padding to narrow/short containers. User-adjusted camera and active playback are preserved during viewport resizing.
- Short landscape screens use a smaller map height; controls/HUD are in document flow.
- Fewer permanent transfer labels on compact maps, with origin/destination/current station retained. Station markers remain available.
- The SVG tradeoff chart scales to its panel; route metric buttons expose information without hover and SVG points support keyboard activation.

## Evidence actually obtained

A Chromium in-app browser at **390×844** displayed the production build with the actual backend data and the existing five 東湖站 → 中原站 routes. Measured document client/scroll width both equaled 390px, map width was 365px and height 422px, native selects were 48px high with 16px text, and buttons met 44px touch targets. The full-page screenshot was visually reviewed: OD selectors, map/selected labels, playback controls, route cards, chart and footer were present without horizontal overlap. Screenshot: `regression/responsive/screenshots/mobile_390x844.png`.

`npm ci` and `npm run build` passed. AST/source comparisons verify unchanged App OD/playback logic, seven map playback functions, route-coordinate extraction, line colors and tradeoff cost calculations. Generic core, model, inputs and formal result bytes remain unchanged. Evidence: `regression/responsive/invariants.json`, `responsive.diff`, and `regression/deployment/verification.json`.

## Checks still pending — do not claim physical-device verification

Further localhost browser access was denied by the browser permission system. Thus the remaining viewport matrix and interaction tests were not performed; no alternative browser/control method was used to bypass that denial.

| Viewport | Status |
| --- | --- |
| 375×667 | Pending |
| 390×844 | Chromium portrait visual/geometry check passed |
| 393×852 | Pending |
| 430×932 | Pending |
| 768×1024 | Pending |
| 820×1180 | Pending |
| 1366×768 | Pending |
| 1440×900 | Pending |
| 1920×1080 | Pending |
| All corresponding landscape/orientation changes | Pending |

Physical **iPhone Safari**, Android Chrome and iPad Safari were not available in this environment. Edge, Firefox, desktop Safari and an actual WebKit engine were not tested. Desktop/mobile layout code and build success are not proof of browser-engine compatibility.

After public deployment, verify real devices: address-bar expansion/collapse; portrait/landscape rotation during playback; notch/home-indicator safe areas; native select picker and no input auto-zoom; pinch/double-tap map zoom and drag; page scrolling beside the map; OD selection/reset; individual route and Play All; final route comparison; chart tap synchronization; no clipped labels/cards/controls; no console/fetch/CORS errors. Play All and these touch/device checks remain pending until actual browser/device verification.

References: [Safari 15.4 viewport units](https://webkit.org/blog/12445/new-webkit-features-in-safari-15-4/), [VisualViewport](https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport), [Leaflet invalidateSize](https://leafletjs.com/reference.html#map-invalidatesize).

Did this change any MOSP algorithm, experimental setting, Taipei Metro assumption, or research result? **No.**
