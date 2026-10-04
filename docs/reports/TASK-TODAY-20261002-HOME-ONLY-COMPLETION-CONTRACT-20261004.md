# 2026-10-02 Home-only completion contract

TASK_ID=TASK-TODAY-20261002-FINAL-PRODUCTION-PUBLICATION
TASK_TYPE=implementation/release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED

## Authority and bounded scope

This is a successor phase of the same Owner-controlled closure, not a new
parallel Production mainline. The Owner authorized necessary bounded fixes,
canonical integration, exact-SHA release and completion of formal 2026-10-02
publication, and subsequently explicitly approved intermediate authorizations.
The development/review model remains SINGLE_OWNER / OWNER_EXCEPTION; no claim
of an independent review, protection change, or waived failing check is made.

Production readback on 2026-10-04 identified a fully collected Owner normal run
with a terminal Home publication failure. This historical observation must be
rechecked through the protected preflight; it is not runtime authority:

- Source run: `8d45de1a-a84a-5d15-88ce-af4f67e69bb9`.
- Source runtime: `74cd2209b85b9f1ded89f147051217941f087e36`.
- Requested/accounted 553; official prices 552; official legitimate suspension 1.
- Provider retries/failures 0; institutional-flow formal readback PASS.
- 45 FORMAL/PIT_FORMAL Topic snapshots PUBLISHED; no formal Score/Grade/Strength
  or Lifecycle success is inferred from their publication.
- Original finality failure: `FORMAL_PUBLICATION_READBACK_NOT_READY`.

Three tightly coupled repairs are in scope:

1. Explicitly request TWSE `MI_INDEX?date=<target>&type=IND&response=json`.
   The otherwise successful response without `type` has empty index table
   placeholders. Preserve exact-date validation, signed-change previous-close
   derivation, raw response provenance and null OHLC. Version the adapter v3.
2. Pass the existing, authoritative date-effective normal execution universe
   into Home breadth/distribution. Do not infer eligibility from price presence.
   The original Home read included 555 registered equities while the existing
   governed normal universe accounted for 553: TPE 6806 and TWO 5371 were outside
   the target execution universe. Unknown/missing/provider failures *inside*
   the governed universe still block publication. Whole-market aggregates and
   covered-stock distribution remain separate authorities and denominators.
3. Add a separate one-shot **Home-only completion** operator contract. This is
   not a second normal execution or a relaxation of OwnerNormalExecution.

## Home-only contract and write set

`home-completion-preflight` is read-only. `home-completion-apply` requires a
separate completion authorization UUID plus the existing explicit Owner write
flag, exact runtime SHA and migration 0048 check. Only target 2026-10-02 is
accepted. Required inputs are:

- Terminal PARTIAL, FULL, MANUAL Owner normal run; original reason is exactly
  the Home formal-publication readback failure, not provider/Topic failure.
- Exact reference/calendar/execution-key lineage and original Owner UUID.
- Continuous immutable checkpoint attempts and matching scope/key/hash format.
- Completed session/readiness/status/official flow/formal Topic checkpoints.
- All ingestion accounted: 552 actual price requests/successes, one legitimate
  unavailable, no failures; non-provider request/failure counters SQL NULL.
- Existing authoritative universe, reconciliation, comparator date/instrument/
  official source/lineage and live formal Topic/institutional-flow readbacks.
- Both newly read official index and aggregate facts valid for the exact date.
- No existing PUBLISHED Home or consumed Home-only completion claim.

The existing date/session transaction claim lock and source-run row lock protect
the claim race. The completion claim is committed **before** the Home writer.
Any marker, including CLAIMED or FAILED after interruption, rejects another
authorization; there is no automatic retry. The collector remains terminal
PARTIAL during completion, never becomes a zombie RUNNING run.

Allowed writes are a new canonical Home envelope/facts/sections for 10/2,
append-only completion/finality checkpoints, the separate claim audit metadata,
and the validated source run's PARTIAL-to-SUCCESS terminal closure **only after
actual Home/formal readback PASS**. Original failure code/state/completion time
are preserved in completion metadata and old failed checkpoint events remain.

No new collector run, provider PRICE ingestion, comparator application, status
resolution, Topic/Score/Grade/Strength/Lifecycle calculation, old-run repair,
historical recovery or backfill is callable through this completion surface.
Original Owner normal `reentryAllowed=False` remains unchanged. Existing normal
duplicate-identity prevention is not changed. Failed completion records retain
exception class, separate failure code and operator action requirement.

## Preserved product and release boundaries

No scoring, Lifecycle, Topic membership, Opportunity, provider price authority,
2601 authority, secret policy, migration, schema, frontend or API contract change.
Home optional downstream unavailable states remain honest; missing Strength or
Lifecycle is not synthesized or promoted from research. Home freshness and
latest-completed-session date rules remain unchanged.

Run 2284, the 10/1 failed run, and the earlier 10/2 partial run remain untouched.
The new normal run's immutable successful provider output is reused without
re-execution. No manual SQL or direct operational UPDATE is authorized.

Candidate validation must cover positive/negative contract cases, actual
PostgreSQL claim/checkpoint/terminal persistence and exception idempotence,
Home scoped coverage, IND request shape, normal/recovery guards, full backend,
frontend/build, OpenAPI/client, migration graph, changed Ruff and diff checks.
Production completion is forbidden until canonical integration, all required
checks and actual three-end exact-SHA readbacks are verified. Code readiness is
not Production completion; retain the operational readback separately.

## Pre-commit diagnostic evidence

The new contract/scoped-Home/request-shape suite passed 66 cases. Separate
disposable PostgreSQL claim/comparator/normal-execution validation passed 16
cases; no Production database was used. Invalid intermediate test invocations
with nonexistent filenames ran zero tests and are not counted as validation.

One existing isolated PostgreSQL test,
`test_post_close_reference_universe_is_313_193_and_excludes_6806`, failed with
`REFERENCE_CONTEXT_NOT_READY` on both the candidate and the exact unmodified
74cd source archive using the same disposable database. Its historical 8/13
reference-context failure is baseline debt, not repaired or suppressed here.
New fixture authoring errors and a negative test that inadvertently exercised
2601's real suspension precedence were corrected before candidate validation;
production authority policy was unchanged.

Final exact-commit full-suite, CI, lineage and deployment results belong in the
dated operational evidence. No candidate or diagnostic result alone authorizes
publication or establishes a runtime SHA.
