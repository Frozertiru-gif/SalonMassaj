# DEF — Performance diagnostics and optimizations (public landing)

## Profiling setup (local, no external services)

1. `npm run dev -- --port 3100` on baseline branch + browser performance capture.
2. `npm run dev -- --port 3101` on optimized branch + same capture.
3. `npm run build` for production route-level JS stats.
4. `node scripts/bundle-report.mjs` for chunk-level approximation for `/`.

## Top-3 root causes of visible lags (before)

1. **Whole landing page was a giant Client Component (`"use client"` in `app/page.tsx`)**.
   - Result: hydration for all blocks (hero + services + why-us + reviews + booking section) and heavy main-thread work.
2. **Cascading client-side fetching with multiple `useEffect` + `setState`**.
   - Result: sequential rerenders while blocks appeared.
   - Fact from baseline dev server logs: duplicated requests in dev for the same endpoints (`/api/public/services`, `/api/public/reviews`, `/api/public/settings/contacts`, `/api/public/weekly-rituals`) during first load.
3. **No caching strategy for public data**.
   - `publicFetch` and proxy handlers used `no-store`, so public content could not benefit from Next fetch cache/revalidation.

## Metrics (before → after)

### Initial JS (observable)

- **DevTools resource transfer for `/_next/static/*.js` while loading `/`**:
  - before: **192,131 bytes**
  - after: **169,683 bytes**
  - delta: **-11.7%**

### Requests duplication

- before: duplicate fetch rounds observed for public endpoints on first load (baseline dev log).
- after: homepage data fetched on the server in one `Promise.allSettled`; browser no longer issues initial `/api/public/*` requests for services/reviews/rituals/contacts.

### Production build route stats

- after (`npm run build`): route `/` has **2.77 kB** route code and **96.6 kB First Load JS** (from Next build table).

### LCP/INP/CLS direction

- Layout stability improved by reserving stable heights for async ritual block (`min-h` + skeleton fallback), reducing visual jumps when content appears.
- Interactivity pressure reduced by moving static sections to Server Components and isolating client JS to interactive blocks only.
