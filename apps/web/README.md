# TopicPilot Platform Web

Public, read-only React interface for the TopicPilot enterprise data platform.

## Local setup

1. Copy `.env.example` to `.env.local`.
2. Set `NEXT_PUBLIC_API_BASE_URL` to the runtime FastAPI origin.
3. Run `npm install` and `npm run dev`.

The optional synthetic fallback is disabled by default. Set
`NEXT_PUBLIC_ENABLE_DEMO_FALLBACK=true` only for an explicitly labelled local
portfolio demonstration. API failures stay visible in production.

## Validation

- `npm run lint`
- `npm run build`
- `npm test`

The site uses the existing vinext/Cloudflare worker build. D1 and R2 remain
unset because the browser reads the separate FastAPI service.
