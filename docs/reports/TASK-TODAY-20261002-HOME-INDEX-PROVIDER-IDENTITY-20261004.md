# Bounded Home index-provider interface alignment

Dated evidence: 2026-10-04. Same Owner-authorized final 10/2 publication task;
E-only existing worktree/branch. Required terminal state remains
POST_DEPLOY_VERIFIED. This implementation report is not a publication claim.

Baseline canonical: 8d6613d13030dde7d3b2cea639aa2b5cbe6f53cc. Exact API, Worker
and public Web runtime verified before READ-ONLY Home-completion preflight.
Preflight stopped with HOME_COMPLETION_INDEX_NOT_READY; no completion claim,
Home write, comparator apply, provider ingestion or second normal run occurred.

Read-only diagnosis obtained AVAILABLE exact-date official TWSE/TPEx indices,
positive finite close/previousClose and response hashes. The existing TPEx
adapter emits source_provider="TPEx", whereas the new Home-only validator
expected "TPEX". A controlled real-fetch/parser-to-validator regression
reproduced HOME_COMPLETION_INDEX_NOT_READY on the unchanged baseline, with
every other index input valid. This deterministic interface mismatch is proven;
the original failed live preflight did not expose individual provider reasons,
so no claim is made that transport could never also fail.

The single production-line change uses the adapter's exact existing identity.
No case folding, arbitrary aliases, endpoint/source/authority change, date-gate
relaxation, retry, new execution or formula change. Unknown providers, uppercase
noncontract aliases, wrong dates, unavailable facts, untrusted endpoints, missing
response hashes/lineage and invalid previousClose still fail closed. Controlled
fixtures are explicitly synthetic; no market prices or credentials are tracked.

The old simplified fixture had repeated the validator's incorrect spelling.
It now follows the actual adapter contract. Twelve added regression cases
exercise real index adapters and negative identity/date/lineage/comparator
gates, without HTTP or Production access. Existing lifecycle/idempotence tests
remain intact. Full baseline: 1302 passed, 77 skipped, 0 failed; candidate count
and CI evidence belong in the task's owning operational report.

Only after clean candidate validation, required CI, Owner-exception merge,
fresh exact-canonical artifact and three-end runtime readback may the same
unconsumed separate Home-only authorization be evaluated again. Never reapply
comparators, repeat normal execution, resume protected old runs, backfill,
activate a scheduler, perform manual SQL or manufacture missing optional fields.
