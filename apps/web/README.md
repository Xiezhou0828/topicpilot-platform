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
npm run preview:review -- --mode iterative
```

`ITERATIVE_LOCAL` is the fast hot-reload mode. It may run from a dirty working
tree and uses the clearly labelled representative synthetic snapshot unless an
explicit read-only API origin is supplied.

For a reproducible candidate using the current formal read API, run:

```bash
npm run preview:review -- --mode exact-sha \
  --candidate-ref <clean-candidate-sha> \
  --read-api-origin https://topicpilot-api.onrender.com
```

`EXACT_SHA_CANDIDATE` requires `HEAD` to equal the requested commit and the
working tree to be clean. The local server listens on `http://localhost:3000`.
The optional local proxy accepts only `GET`/`HEAD` requests for the fixed
read-only API prefixes, strips credential-like headers, and never grants
writer or Production mutation authority. Stop either mode with `Ctrl+C`.
