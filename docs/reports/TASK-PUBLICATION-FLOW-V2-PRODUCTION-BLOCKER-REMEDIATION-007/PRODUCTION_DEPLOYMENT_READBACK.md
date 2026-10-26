# Production deployment and readback

## Current Render identity

API service: topicpilot-api, service ID srv-d9tvnm740ujc73f7vmf0.

- Live commit: 9703c956....
- Live deploy: dep-db3vkkij9qps73domakg.
- Origin: https://topicpilot-api.onrender.com
- Dashboard: https://dashboard.render.com/web/srv-d9tvnm740ujc73f7vmf0/deploys/dep-db3vkkij9qps73domakg

Worker service: topicpilot-live, service ID srv-da6okdpsrm7s73aqbnn0.

- Live commit: 9703c956....
- Live deploy: dep-db3vkl7f3r2c73domakg.
- Dashboard: https://dashboard.render.com/worker/srv-da6okdpsrm7s73aqbnn0/deploys/dep-db3vkl7f3r2c73domakg

## Smoke/readback

- API health/readiness remained available in the dashboard.
- GET /api/v2/topics returned HTTP 500.
- Individual Topic reads remained mixed: known deferred rows returned 500, AI PCB returned 200, and an absent label returned 404.
- Worker logs showed provider wait followed by repeated blocked reference preflight events.

No Task 007 deployment, manual deploy, scheduler activation, publication, replay, migration, or Production DB mutation occurred.

DEPLOYMENT_RESULT=NOT_REQUIRED
PRODUCTION_API_SHA=9703c956...
PRODUCTION_WORKER_SHA=9703c956...

## API exception readback

Render application logs for the live API (commit 9703c956...) show `[ghnfx]` requests at 2026-10-09 04:39:48 GMT+8 returning HTTP 500. The traceback reaches `production_read_model_api.py:147` and ends in `fastapi.exceptions.ResponseValidationError`; the representative path is `response.items[20].ownerSeededV0.asOfDate`, where the input is `datetime.date(2026, 10, 7)` but the schema requires a string. The live API has not been redeployed with the isolated fix.

The same log stream has no explicit request ID beyond the Render correlation group and no SQLSTATE for this response-validation failure.
