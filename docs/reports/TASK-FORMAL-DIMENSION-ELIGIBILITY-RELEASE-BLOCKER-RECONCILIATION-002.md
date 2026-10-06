# TASK-FORMAL-DIMENSION-ELIGIBILITY-RELEASE-BLOCKER-RECONCILIATION-002

Verification date: 2026-10-06, Asia/Taipei.

This report resumes the existing release-blocker lineage. It does not replace
the original failed execution, does not touch the protected Preview worktree,
and does not perform Production deployment, migration, scheduler mutation,
target-date recovery, formal publication, or downstream data writes.

```text
TASK_ID=TASK-FORMAL-DIMENSION-ELIGIBILITY-RELEASE-BLOCKER-RECONCILIATION-002
TASK_STATUS=BLOCKED_RELEASE_BLOCKER_RECONCILIATION
TARGET_DATE=2026-10-05
ORIGINAL_FAILED_EXECUTION_PRESERVED=YES
ORIGINAL_RECOVERY_EXECUTION_PRESERVED=YES
ORIGINAL_RECOVERY_EXECUTION_ID=5890eda0-c81b-50d8-9cfc-05e5a6e7b5a0
PREVIEW_WORKTREE_TOUCHED=NO
PREVIEW_WORKTREE_ISOLATED=YES
RELEASE_WORKTREE_CONFIRMED=C:\Users\acer\Desktop\題材領航\topicpilot-platform
RELEASE_BRANCH=codex/formal-dimension-release-blocker-reconciliation-002
RELEASE_HEAD=d568fca2e00a9b20a2f42056ecc43ff0104276ed
ORIGIN_MAIN=e97f590cad497c0a23fb027fce39ec5891ea4bc1
PUSH_STATUS=NOT_PERFORMED
```

## 1. Existing lineage and integration

The Release checkout was independently identified before any integration work.
The protected Preview checkout remains at
`C:\Users\acer\Desktop\題材領航\topicpilot-preview-v1-1-flat-canvas`,
detached at `7dfb34d10f299de2d203abd7756294e0e1ecda4e`; it was only listed for
isolation verification and was not entered, checked out, reset, cleaned,
stashed, merged, committed, or restarted.

The fetched canonical remote `main` is `e97f590cad497c0a23fb027fce39ec5891ea4bc1`.
The prior local implementation candidate `c3bb8b020059b4b5113d0f814dab1268c2e92345`
was not present on GitHub. Its implementation parent
`04ad3e3c7e4840cad2bf4643369162a0affdc956` was cherry-picked onto the fetched
canonical main and produced the current Release head `d568fca` without a
conflict.

Remote-only history identified during reconciliation was preserved in the
integration base, rather than overwritten:

- `392afd9 docs-close-daily-publication-activation-evidence`
- `c43336c docs-correct-activation-base`
- `27c1343 resolve-activation-report-merge`
- `e97f590` merge of the current canonical main lineage

The current Release branch is one commit ahead of `origin/main` and has no
tracked modifications. Three earlier task reports remain intentionally
untracked and preserved; they were not staged or altered.

## 2. Candidate scope and policy preservation

The integrated candidate contains the already-approved dimension-scoped
corporate-action comparator implementation. It adds typed dimension
eligibility, an explicit `ACCOUNTED_UNAVAILABLE` comparator state for the
governed official corporate-action boundary, exact prior formal-session
resolution without forward-fill across suspension, and dimension-scoped
strength exclusion. It preserves membership, role/sample, benchmark
independence, Grade's Absolute dependency, chronological Lifecycle semantics,
and fail-closed provider/date/finality authority.

No 2601-specific special case, synthetic close, ad-hoc importer, unofficial
source, migration, scheduler change, historical Home publication, or runtime
configuration mutation was added by this reconciliation.

## 3. Worker failure reproduction and root-cause classification

The exact current Release head was tested with the existing cold-process
boundary suite from `services/api`:

```text
PYTHONPATH=src;../..
py -3.12 -m pytest -q tests/test_worker_import_boundary.py
3 failed, 11 passed, 162.33s
```

Observed failures:

1. Cold `topicpilot_api.live.cli` import: `subprocess.TimeoutExpired` after
   30 seconds, with no useful child output.
2. Cold `topicpilot_api.provider_preflight_cli` import: Windows process return
   code `3221227274` (`0xC000070A`), with empty stdout and stderr.
3. Cold Worker `--dry-run --mode post-close`: the same `0xC000070A` return
   code, with empty stdout and stderr.

The test intentionally starts a clean Python 3.12 `-I -B -c` child, removes
database/vendor credential variables, inserts only the API source path, and
monkeypatches socket connects to fail. The failure occurs before a Python
assertion or provider/database call can produce an application-level error.

The preserved clean baseline evidence shows the same boundary class and the
same three affected families: `3 failed, 11 passed` in 308.81 seconds. The
current candidate therefore does not introduce a deterministic new failure in
the unchanged `live.cli` path. The exact current failure is classified as:

```text
WORKER_FAILURE_CLASS=WINDOWS_LOCAL_COLD_PROCESS_HARNESS_OR_ENVIRONMENT_DEPENDENCY
WORKER_FAILURE_IS_CANDIDATE_REGRESSION=NOT_PROVEN / evidence weighs against
WORKER_FAILURE_IS_PRODUCTION_RUNTIME_DEFECT=NOT_PROVEN
WORKER_FAILURE_IS_RELEASE_GATE_PASS=NO
```

This classification does not waive the gate. It records that the local
Windows process boundary is not a valid proof of candidate Worker readiness.
The current canonical Ubuntu CI for `origin/main` succeeded, including the
backend test job, but that run did not execute the unreleased candidate head.
Consequently, candidate-specific Linux CI and candidate protected-runtime
readback remain required evidence and are not inferred from baseline success.

Additional local evidence:

- Candidate focused implementation chain: `85 passed, 1 skipped`.
- Earlier full candidate run: `1,350 passed, 79 skipped, 7 failed`; the two
  Worker cold-process failures were the same Windows process-boundary class,
  and five failures were absent research fixtures, not release-path
  assertion failures.
- Current remote-main CI run `37342658154` for `e97f590` completed SUCCESS for
  Backend/migration/OpenAPI, Frontend, Docker Compose smoke, and Secret scan.

No bounded code fix was applied because the evidence points to the Windows
test harness/process environment, while changing Worker startup or replacing
the cold-process guard would alter a protected runtime boundary without a
reproducible application defect.

## 4. Canonical G2 and provider/date/finality authority

The separately authorized G2 reference-authority remediation is preserved and
was re-read as the canonical prerequisite. Its exact ACTIVE binding is:

```text
G2_REVALIDATED=YES
G2_REFERENCE_VERSION=tw-reference-v1-rollover-0578862f98914eb7
G2_REFERENCE_ACTIVE=YES
G2_REFERENCE_LOAD_STATUS=READY
G2_MARKETS=2
G2_INSTRUMENTS=555
G2_MISSING=0
G2_DUPLICATES=0
G2_TARGET_DATE_IS_SESSION=true
G2_TARGET_DATE_REASON=null
G2_API_WORKER_BINDING_EXACT=YES
G2_PRODUCTION_WRITE_SET=[]
```

This G2 result proves reference authority and the session decision only. It
does not prove target-date EOD facts, benchmark facts, or finality.

The canonical read-only provider preflight remains FAIL:

```text
PROVIDER_DATE_AUTHORITY=FAIL_CLOSED / target-date official rows matched
PROVIDER_FINALITY_AUTHORITY=NOT_PROVEN
PROVIDER_PREFLIGHT_STATUS=FAIL
PROVIDER_PREFLIGHT_READ_ONLY=YES
TPE_PROVIDER_AUTHORITY=TWSE_OFFICIAL_DAILY
TPE_PROVIDER_VERSION=twse-official-daily.v2
TPE_TARGET_DATE_MATCHED=true
TPE_TARGET_DATE_COVERED=347
TPE_FINALITY_ERROR=PREVIOUS_CLOSE_AUTHORITY_NOT_READY
TWO_PROVIDER_AUTHORITY=TPEX_OFFICIAL_DAILY
TWO_PROVIDER_VERSION=tpex-official-openapi-daily.v1
TWO_TARGET_DATE_MATCHED=true
TWO_TARGET_DATE_COVERED=206
TARGET_DATE_EOD_RECOVERED=NO
BENCHMARK_RECOVERED=NO
```

The precise blocking authority is the missing formal previous-close evidence
for the expected TPE instrument 2601. Its corporate-action/trading-suspension
status was accounted for as a governed status, but the target date resumed and
there is no admitted exact prior formal close. HTTP success and target-date
row matching therefore do not establish finality. This remains a STOP
condition under the canonical provider contract.

## 5. Protected Production evidence boundary

The preserved Production readbacks show the deployed baseline API and Worker
at `6fff533168b1823052071f6d88d1f266397d327d`, migration head
`0049_task_daily_formal_publication_receipt`, healthy API readiness, and the
restored G2 binding above. The preserved activation evidence also records the
existing Render Background Worker and no competing scheduler.

Those readbacks are not a readback of candidate `d568fca`: no candidate
deployment was authorized or performed. Therefore:

```text
PROTECTED_RUNTIME_READBACK_READY=NO_FOR_CANDIDATE
API_PRODUCTION_READBACK=BASELINE_6fff533_READ_ONLY
WORKER_PRODUCTION_READBACK=BASELINE_6fff533_PRESERVED_READ_ONLY
ALEMBIC_PRODUCTION_READBACK=0049_task_daily_formal_publication_receipt
SCHEDULER_MUTATION=NO
COMPETING_SCHEDULER_CHANGE=NO
```

The release gate cannot treat a baseline Production readback as proof that
the unreleased candidate is deployed or runnable in the protected Worker.

## 6. Release readiness matrix

| Gate | Result | Evidence / disposition |
|---|---|---|
| Original failed execution preserved | PASS | Existing recovery report and execution lineage retained. |
| Release worktree identified | PASS | Dedicated Release checkout confirmed; Preview untouched. |
| Remote history preserved | PASS | Fetched `origin/main=e97f590`; approved implementation cherry-picked without conflict. |
| Candidate focused tests | PASS | `85 passed, 1 skipped`. |
| Worker cold-process boundary | BLOCKED | `3 failed, 11 passed`; Windows `0xC000070A`/timeout class reproduced. |
| Candidate Linux CI | NOT RUN | Current successful run is for `origin/main`, not `d568fca`. |
| Candidate protected API/Worker readback | NOT READY | Candidate was not deployed; baseline readback cannot substitute. |
| Canonical G2 reference authority | PASS | Active exact version, READY, 2 markets, 555 instruments, no missing/duplicates. |
| Provider target-date EOD authority | BLOCKED | Official rows matched, but provider preflight FAIL. |
| Provider finality authority | BLOCKED | 2601 exact prior formal close not admitted. |
| Reconciliation/publication/replay | NOT RUN | Must remain downstream of provider/date/finality PASS. |
| Canonical main push | NOT PERFORMED | Fail-closed because required release gates are not complete. |

## 7. Required terminal fields

```text
TASK_STATUS=BLOCKED_RELEASE_BLOCKER_RECONCILIATION
TARGET_DATE=2026-10-05
G2_REVALIDATED=YES
PROVIDER_DATE_AUTHORITY=FAIL_CLOSED
PROVIDER_FINALITY_AUTHORITY=NOT_PROVEN
TARGET_DATE_EOD_RECOVERED=NO
BENCHMARK_RECOVERED=NO
RECONCILIATION_STATUS=NOT_RUN / provider-date-finality gate failed
FORMAL_TOPIC_SNAPSHOT_STATUS=NOT_RUN
ABSOLUTE_STATUS=NOT_RUN
RELATIVE_STATUS=NOT_RUN
FORMAL_GRADE_STATUS=NOT_RUN
LIFECYCLE_REPLAY_STATUS=NOT_RUN
RECEIPT_LINEAGE_STATUS=NOT_CREATED; original failed execution preserved
HISTORICAL_HOME_REPUBLISHED=NO
ORIGINAL_FAILED_EXECUTION_PRESERVED=YES
PRODUCTION_WRITE_SET=NONE
PROTECTED_PREVIEW_WRITE_SET=NONE
RELEASE_WORKTREE_WRITE_SET=report only; no Production write
NEXT_ACTION=STOP fail-closed. Obtain canonical official exact prior formal-close/finality evidence for TPE 2601, then run candidate Linux CI and protected candidate runtime readback before any canonical main push. Do not perform target-date recovery, publication, Lifecycle replay, scheduler mutation, deployment, migration, or historical Home republish.
```
