# Cold-start loading experience

On initial opening, the frontend checks `/api/health` before loading stations,
the network and the initial 東湖站 → 中原站 Pareto routes. Both `ok` and
`pareto_csv_found` must be true. All initial data must arrive before controls
and result interactions become available. The initial routes are used directly,
without a duplicate automatic search or any route transformation.

The loading card appears above the disabled OD controls and says:

> 正在載入臺北捷運 Pareto 路徑資料…
>
> 首次開啟時伺服器可能需要一些時間啟動，請稍候。

Transient network errors, timeouts and unavailable initial data automatically
retry after **3 seconds**. Each request (including its JSON body) is limited
to **12 seconds**; the entire startup is limited to **3 minutes**. Retrying is
visible, and successful recovery opens the normal interface automatically.
After the total limit, a friendly message and **重新嘗試** button start a fresh
attempt without reloading the page. Raw initial `Failed to fetch` is not shown.

Unmount/React StrictMode cleanup cancels pending requests and retry timers.
A failed batch cancels sibling requests before retrying. Retry is only applied
to startup; subsequent searches and animation behavior retain their existing
logic. No polling continues after successful startup.

The loading card uses a polite accessible status, wrapping text, flexible width
and the existing safe-area spacing. Its small spinner becomes static when
reduced motion is requested. There is no fixed-height fullscreen loading panel.

Verification commands (Node 24, from this frontend directory):

```sh
npm run test:startup
npm run build
```

The fault-injection tests cover warm startup, network errors, health readiness,
hanging requests, initial route errors, cancellation, total deadline and manual
recovery. Research/core/input/result files and existing map, route panel,
tradeoff plot and playback functions are checked against pre-change snapshots.
Verification passed: **11/11 startup tests**, Vite production build,
**92/92 protected file hashes** and **20/20 unchanged callback/constant AST
comparisons**. A local fault proxy returned repeated health 503s; the browser
displayed retries with all four selectors/Search disabled. After restoring the
local backend, the same page automatically displayed the map and all five
東湖站 → 中原站 routes, with one initial routes request and no refresh.
Loading viewports **320×568**, **390×844**, and **844×390** had no horizontal
overflow. Physical iOS Safari/Android checks are not implied by these tests.
