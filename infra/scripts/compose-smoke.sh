#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  docker compose logs --no-color web api migrate seed postgres 2>/dev/null || true
  docker compose down --volumes --remove-orphans
}
trap cleanup EXIT

docker compose config --quiet
docker compose build api web
docker compose up -d postgres
docker compose run --rm migrate
docker compose run --rm seed
docker compose up -d api web

for attempt in $(seq 1 30); do
  if curl --fail --silent --show-error http://localhost:8000/healthz >/dev/null \
      && curl --fail --silent --show-error http://localhost:3000 >/dev/null; then
    curl --fail --silent --show-error http://localhost:8000/readyz >/dev/null
    curl --fail --silent --show-error http://localhost:8000/api/v1/stocks?limit=1 \
      | grep --quiet 'DEMO-'
    echo "Compose smoke test passed for PostgreSQL, API, and Web."
    exit 0
  fi
  sleep 2
done

echo "API did not become healthy within 60 seconds." >&2
exit 1
