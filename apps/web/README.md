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
