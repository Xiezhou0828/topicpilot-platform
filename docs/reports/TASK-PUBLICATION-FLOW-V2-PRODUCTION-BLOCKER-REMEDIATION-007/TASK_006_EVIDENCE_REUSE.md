# Task 006 evidence reuse

Source package:
E:/TopicPilot/w/publication-flow-v2-runtime-closure-006/docs/reports/TASK-PUBLICATION-FLOW-V2-PRODUCTION-RUNTIME-CLOSURE-AND-FIRST-LIVE-CYCLE-006/

## Reused findings

- Task 006 verified API runtime SHA 9703c956... and migration 0050_task_purge_retired_topics as the historical runtime readback.
- Task 006 observed V2 stocks and topic-catalog succeeding while V2 topics returned 500.
- Task 006 correctly left the Topics root cause UNKNOWN and made no speculative Production patch.
- Task 006 documented the durable receipt/result contract, non-success CLI exit semantics, and the no-manual-publication boundary.
- Task 006 left scheduler activation blocked pending Worker identity, recovery readiness, and Topics API evidence.

## New evidence that changes the closure picture

1. Render Dashboard now independently exposes both live service revisions. API and Worker are both running 9703c956..., so Worker identity is no longer UNKNOWN, but it is not equal to the current canonical fc11856....
2. Render API logs confirm repeated 500 responses for both the collection route and data-dependent slug routes. They still do not expose the server traceback.
3. A bounded forensic readback was added and merged. It returns sanitized failure layers, but the forensic database role lacks SELECT on the core formal tables, so the artifact proves an access blocker rather than the API route root cause.
4. Worker logs show a later fail-closed reference preflight rollback error. This is an additional runtime blocker that was not available in the Task 006 public readback.

Task 006 remains the authority for the historical receipt and publication contract; Task 007 does not replay or republish 2026-10-08.
