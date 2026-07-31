# Screenshot and demo capture checklist

The public portfolio reuses the original TopicPilot interface. Do not document
or capture the retired replacement dashboard as if it were a separate product.
Do not add fabricated screenshots or unverified deployment URLs.

Capture these artifacts after the synthetic stack and public deployment pass:

1. `01-home.png` — the original TopicPilot home and market overview.
2. `02-topics.png` — topic strength and 14-day rotation in the original UI.
3. `03-watchlist.png` — strategy candidates in the original watchlist layout.
4. `04-stock-detail.png` — one synthetic issuer detail page.
5. `05-data-quality.png` — the original UI's freshness and quality indicators.
6. `06-openapi.png` — FastAPI documentation with read-only routes.
7. `07-ci.png` — a successful CI run without exposing repository secrets.
8. `08-power-bi-overview.png` — synthetic Power BI report after validation.

Requirements:

- Use synthetic data only and keep the synthetic-data label visible.
- Use a desktop width near 1440 px and capture a second mobile example for the
  web portfolio if responsive layout is a claimed feature.
- Crop browser account information, local usernames, tokens, private tabs, and
  development tool panes.
- Add concise alt text when embedding the images in README or portfolio pages.
- Record a separate three-to-five-minute walkthrough; do not commit a large
  video binary when an external portfolio host is used.
