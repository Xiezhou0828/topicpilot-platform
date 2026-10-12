/** Safe, read-only defaults for the human-facing local Preview Review lane. */
export const DEFAULT_PREVIEW_REVIEW_PORT = 4317;
export const DEFAULT_READ_ONLY_API_ORIGIN = "https://topicpilot-api.onrender.com";

export const PREVIEW_REVIEW_USAGE = `TopicPilot Preview Review

Quick start:
  npm run preview:review

Defaults:
  mode              iterative local review
  port              ${DEFAULT_PREVIEW_REVIEW_PORT}
  data              real formal API · read only
  diagnostics       off
  URL               http://localhost:${DEFAULT_PREVIEW_REVIEW_PORT}

Advanced overrides:
  npm run preview:review -- --mode iterative --read-api-origin <origin> --port <port>
  npm run preview:review -- --mode iterative --read-api-origin <origin> --financial-api-origin <local-origin> --port <port>
  npm run preview:review -- --mode exact-sha --candidate-ref <sha> --read-api-origin <origin>
  npm run preview:review -- --help

The Preview proxy accepts only GET/HEAD requests for the allowlisted read paths.
It never forwards credentials and never grants Production write authority.
The optional financial API origin is also read-only and is intended for an
isolated non-Production financial read model when the main Preview target does
not yet expose the financial routes.`;
