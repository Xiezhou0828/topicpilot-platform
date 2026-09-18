# F1-F9 Recovery Map

This map is the compact, evidence-first index for `TASK-F1-F9-HISTORICAL-CANONICAL-RECOVERY-001`. It deliberately separates historical existence, current canonical presence, and future disposition.

## Authority anchors

| Question | Authoritative evidence | Result |
|---|---|---|
| What repository is canonical? | `AGENTS.md`, current governance state | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| What is the governed mainline? | `CURRENT_PROJECT_STATE.md` | `origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` |
| What is the development integration base? | `CURRENT_PROJECT_STATE.md`, branch matrix | `a8357d46194f9669709f184949270e20a7a2546c` |
| What is the isolated recovery base? | this task manifest | `beb5b3d850bb8def248239f829abe39bcd24979b` |
| Where are F4-F9 artifacts? | full-history path logs | aggregate snapshot `1501468da8b7b4d8338ae1c2da23996126ee918c` on two Today refs |
| Were F4-F9 promoted to Production? | each historical report and current release state | no; all evidence is development/branch-only |
| Were F1-F3 recovered? | all-ref path, subject, pickaxe, and alias searches | no recoverable identity; conservative `UNKNOWN` |

## Item matrix

| Item | Historical evidence | Best reachable implementation evidence | Historical status | Current canonical status | Disposition | Future owner / lane |
|---|---|---|---|---|---|---|
| F1 | no report, path, message, or alias hit | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | owner packet required before any claim |
| F2 | no report, path, message, or alias hit | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | owner packet required before any claim |
| F3 | no report, path, message, or alias hit | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | owner packet required before any claim |
| F4 | closure report in aggregate Today snapshot | `1501468` snapshot; individual task SHA not recoverable | branch-only PASS closure | partially present in Today/Home contracts and state scaffolding; dedicated consumer not canonical | `MERGE` | Today / Integration; serial read-authority reconciliation |
| F5 | closure report in aggregate Today snapshot | `1501468` snapshot; individual task SHA not recoverable | branch-only PASS closure | partially present as current V2 status surfaces, but exact shared mapper is not canonical | `MERGE` | Frontend / Integration; shared-surface reconciliation |
| F6 | closure report in aggregate Today snapshot | `1501468` snapshot; individual task SHA not recoverable | branch-only PASS closure | partially present in current Stock formal EOD/history/read views; exact historical consumer is not canonical | `MERGE` | Stock / WS2; serial Stock read-view reconciliation |
| F7 | closure report in aggregate Today snapshot | `1501468` snapshot; individual task SHA not recoverable | branch-only PASS closure | formal backend Technical V0 exists; historical fixed-indicator consumer is not canonical | `MERGE` | WS2 / Stock technical; serial provider-consumer reconciliation |
| F8 | closure report in aggregate Today snapshot | `1501468` snapshot; individual task SHA not recoverable | branch-only PASS closure | current V2 navigation exists, but exact historical commercial boundary behavior is not canonical | `MERGE` | Frontend / Integration; serial navigation reconciliation |
| F9 | blocked closure report in aggregate Today snapshot | `1501468` snapshot; individual task SHA not recoverable | branch-only blocked artifact | current Topic catalog provider exists, but the historical frontend consumer and B2 authority path are not canonical | `MERGE` | Topic/B2 + Integration; wait for B2 authority and serial consumer work |

## Aggregate historical source

`1501468da8b7b4d8338ae1c2da23996126ee918c` is the only reachable object found containing all six F4-F9 formal reports and the associated aggregate implementation snapshot. It is reachable from:

- `origin/codex/today-commercial-investor-release-20260912` at `569d2b4d5f4b94c2ab403a440e8b4b02c2fd2586`.
- `origin/codex/today-production-convergence-20260913` at `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b`.

The snapshot is not an ancestor of `origin/main`, the current GOV-003 runtime tip, or the development integration base. It is therefore preserved as historical evidence, not promoted as canonical. Each report’s `EXACT_SHA_BEFORE` is recorded, but the “after” value is self-referential or absent from the report; the six individual before/after commits are not present in the current object database. The aggregate SHA must not be relabeled as six task commits.

## Historical dependency chain

The reports’ own baseline references establish this recoverable sequence:

```text
F4 Today official market fields
  -> F6 Stock formal read view
  -> F5 shared commercial state semantics
  -> F7 formal technical evidence consumer
  -> F8 commercial UX/navigation
  -> F9 read-only commercial beta integration
```

This is a report-baseline chain, not proof of canonical integration. F9 additionally depended on a Topic catalog provider that was absent from its exact committed baseline and present only in the dirty tree.

## Current dependency graph

```text
Home market index/turnover contract + source authority
  -> Today consumer (F4 merge candidate)

Current V2 state vocabulary and backend reason metadata
  -> Today / Topic / Stock state rendering (F5 merge candidate)

Formal Stock identity + EOD + raw history + topic relations
  -> Stock Explorer / Drawer / detail (F6 merge candidate)
  -> Stock technical read surface (F7 merge candidate)

Formal Technical V0 publication and indicator policy
  -> fixed-indicator consumer with source/as-of/status (F7 merge candidate)

Accepted V2 commercial routes and truthful publication boundaries
  -> Today / Topic / Stock navigation (F8 merge candidate)

B2 formal Topic authority + current Topic catalog provider
  -> Topic list/detail/snapshot consumer
  -> market-aware Topic-to-Stock links (F9 merge candidate)
```

## Boundary decisions

- F1-F3 are not reopened, invented, or marked “not implemented.” They remain `UNKNOWN` until an owner supplies evidence outside the reachable repository or explicitly retires them.
- F4-F9 are not reopened as historical tasks. Their reports remain branch-only evidence; any implementation is a new owner-approved bounded task under the current workstream owner.
- No F-series item owns migrations, Post-Close, scheduler/orchestrator work, Opportunity algorithms, B2 role/score authority, or FUND-001 institutional-flow work.
- `FUND-001_REUSABLE_HISTORY=NO`: the F reports explicitly leave institutional flow separate/unchanged/deferred; incidental legacy fields do not establish reusable formal F-series history.
- `A10_A9_OVERLAP=BOUNDARY_ONLY`: F4 reads freshness/as-of semantics but does not implement the writer, scheduler, persistence, or migration path.

## Future execution buckets

| Bucket | Items | Condition |
|---|---|---|
| `SAFE_TO_RUN_NOW` | recovery map only | read-only archaeology and governance registration are complete |
| `WAIT_FOR_B2` | F9; any F6/F8 Topic-role extension | B2 formal role/authority and publication contract must be accepted first |
| `WAIT_FOR_A9` | none | do not duplicate A9/A10; F4’s freshness dependency is a read contract, not a writer task |
| `WAIT_FOR_OPPORTUNITY` | none | F8 may disclose the boundary but must not activate Opportunity |
| `SERIAL_INTEGRATION_REQUIRED` | F4-F9 | shared frontend/API/generated-client/Topic/Stock surfaces require one owner at a time |

## Canonicalization rule

After these reports, the labels F1-F9 are historical provenance only. The current architecture should be described by its owning capability—Today/Home, shared V2 state, Stock formal read, WS2 Technical V0, V2 navigation, and Topic/B2—rather than by treating the old sequence as a current product taxonomy.
