# TopicPilot Platform Web

Public, read-only React interface for the TopicPilot enterprise data platform.
This app reuses the original TopicPilot navigation, routes, styling, stock
views, favorites, guide, and AI Studio. The migration changes only the shared
snapshot data layer; it does not maintain a second frontend design.

## Local setup

1. Copy `.env.example` to `.env.local`.
2. Set `NEXT_PUBLIC_API_BASE_URL` to the runtime FastAPI origin.
3. Run `npm install` and `npm run dev`.

The public portfolio enables the clearly labelled synthetic fallback by
default. Set `NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=false` only in an environment
that must fail closed when FastAPI is unavailable. The fallback is generated
from `fixtures/demo` and never contains the private TopicPilot snapshot.

## Validation

- `npm run lint`
- `npm run demo:snapshot:check`
- `npm run build`
- `npm test`

The site uses the existing vinext/Cloudflare worker build. D1 and R2 remain
unset because the browser reads the separate FastAPI service.

## Local Preview review environment

From the repository root, use the bounded review runner when a human needs to
review the product locally:

```bash
npm run preview:review
```

The zero-argument command starts `ITERATIVE_LOCAL` on `http://localhost:4317`
with real formal data through the fixed read-only proxy and diagnostics off. It
may run from a dirty working tree. The proxy rejects mutations and forwards no
credentials.

For a reproducible candidate using the current formal read API, run:

```bash
npm run preview:review -- --mode exact-sha \
  --candidate-ref <clean-candidate-sha> \
  --read-api-origin https://topicpilot-api.onrender.com
```

`EXACT_SHA_CANDIDATE` requires `HEAD` to equal the requested commit and the
working tree to be clean. The local server listens on `http://localhost:4317`
by default.
The optional local proxy accepts only `GET`/`HEAD` requests for the fixed
read-only API prefixes, strips credential-like headers, and never grants
writer or Production mutation authority. Use `npm run preview:review -- --help`
for advanced overrides. Stop either mode with `Ctrl+C`.

When the selected read API does not yet expose the Company Research V3
financial routes, keep stock/topic reads on the selected read API and point the
financial readout at an isolated local API instead:

```bash
npm run preview:review -- --mode iterative \
  --read-api-origin https://topicpilot-api.onrender.com \
  --financial-api-origin http://127.0.0.1:8001 \
  --port 4320
```

The financial origin is used only by the five GET/HEAD financial read calls;
it does not replace the formal stock API, does not write to a database, and
does not turn Preview research into published data.
