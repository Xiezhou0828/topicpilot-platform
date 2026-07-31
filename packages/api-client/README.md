# `@topicpilot/api-client`

This package is generated from FastAPI's committed `openapi.json`. It is the
wire-level contract shared by the API and React application; the UI may map
these generated response types into smaller presentation models.

Regenerate after an intentional API change:

```bash
python infra/scripts/check_openapi_drift.py \
  --app topicpilot_api.main:app \
  --write packages/api-client/openapi.json
npm ci --prefix packages/api-client
npm run generate --prefix packages/api-client
```

`scripts/sync-to-web.mjs` copies the generated declaration into the Sites
application because the deployable `apps/web` artifact must be self-contained.
Generated files are reviewed as diffs and must not be edited manually.
