# Screenshot and demo capture checklist

`dashboard.png` is a browser-verified capture of the public synthetic-data
deployment. Do not add fabricated screenshots or unverified deployment URLs.

Capture these artifacts after the synthetic stack and public deployment pass:

1. `01-overview.png` — full-width overview showing the synthetic-data badge.
2. `02-topic-rotation.png` — 14-day topic rotation page with filters visible.
3. `03-strategy-candidates.png` — one of the six strategy candidate pages.
4. `04-data-status.png` — bundle version, data date, freshness, and quality.
5. `05-openapi.png` — FastAPI documentation with read-only routes.
6. `06-ci.png` — a successful CI run without exposing repository secrets.
7. `07-power-bi-overview.png` — synthetic Power BI report after validation.

Requirements:

- Use synthetic data only and keep the synthetic-data label visible.
- Use a desktop width near 1440 px and capture a second mobile example for the
  web portfolio if responsive layout is a claimed feature.
- Crop browser account information, local usernames, tokens, private tabs, and
  development tool panes.
- Add concise alt text when embedding the images in README or portfolio pages.
- Record a separate three-to-five-minute walkthrough; do not commit a large
  video binary when an external portfolio host is used.
