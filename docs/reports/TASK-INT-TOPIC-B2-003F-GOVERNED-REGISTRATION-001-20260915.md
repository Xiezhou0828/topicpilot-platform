# TASK-INT-TOPIC-B2-003F-GOVERNED-REGISTRATION-001

Date: 2026-09-15
Role: Integration Owner
Result: COMPLETE for the bounded 003F governed-registration scope; formal publication remains explicitly blocked.

## Closeout decision

The 003F evidence chain is now durably registered in the current GOV-003
development lineage. The registration preserves the historical implementation
and governance SHAs, records the unique owner-manual authority and its exact
source/canonical hashes, binds the existing B2 authority artifacts and
cardinality, and makes the lifecycle state recoverable from current repository
Project Memory.

This is a governance registration and reconciliation closeout. It is not a
product integration, formal Topic publication, database readback, taxonomy
sync, deployment, or Production activation.

```text
003F_AUTHORITY=VERIFIED
003F_PROVENANCE=COMPLETE
003F_EXACT_SHA_REGISTRATION=COMPLETE
003F_ARTIFACT_HASHES=VERIFIED
003F_CARDINALITY=VERIFIED
003F_PROJECT_MEMORY=RECOVERABLE
003F_CURRENT_GOVERNED_LINEAGE=REGISTERED
FORMAL_PUBLICATION=NOT_ACTIVE
OWNER_DECISION_REQUIRED=NO
INTEGRATION_OWNER_ACTION_REQUIRED=NO_FOR_THIS_BOUNDED_TASK
```

## Baseline and governed execution identity

All changes in this closeout were made only in the dedicated E: worktree:

```text
WORKTREE=E:\topicpilot-worktrees\int-topic-b2-003f-governed-registration-001-20260915
BRANCH=codex/task-int-topic-b2-003f-governed-registration-001-20260915
EXECUTION_BASE_SHA=c3405736e345c670f2eaa5c1eb34b76f61a58ee7
GOVERNED_DEVELOPMENT_BASE_SHA=a8357d46194f9669709f184949270e20a7a2546c
QUALIFIED_GOV003_BASELINE_SHA=2a062d2830dfac4ba2c6c3d25d2c12d0c9fc29b0
CANONICAL_MAIN_SHA=b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40
C_OWNER_CHECKOUT_MUTATED=NO
PUSH=NO
PRODUCTION=UNTOUCHED
```

The C: owner checkout was inspected read-only. Its pre-existing dirty and
untracked owner changes were preserved. The current GOV-003 qualified E:
baseline is the only execution base used for this registration; no newer
baseline was invented.

The historical 003F source task remains identifiable at:

```text
SOURCE_WORKTREE=E:\TopicPilot\worktrees\b2-003f-prov-001-20260914
SOURCE_BRANCH=codex/topic-b2-003f-canonical-provenance-001-20260914
SOURCE_TASK_EXECUTION_BASE=bf7f06741bf701ed46a3fb11aed45fa5755af964
SOURCE_HEAD=34fb7306378395cd6f9ef1aa83343ec79d9c4404
```

## Authority assessment and artifact lineage

The exact owner-manual path in the C: checkout was confirmed as the unique
003F candidate. No conflicting manual authority was found. The companion work
order, committed status ledgers, prior B2 reports, and runtime consumer
references support the same candidate; consumers and prior reports were not
treated as competing authority.

The historical source chain was imported into the current E: Git object store
as evidence refs only. No historical product files were replayed into the
current working tree. The relevant commits and bounded diffs are:

| SHA | Subject / role | Changed surface |
| --- | --- | --- |
| `bf7f06741bf701ed46a3fb11aed45fa5755af964` | B2 canonical artifact publication gate evidence | One B2 gate report; records `BLOCKED_BY_FORMAL_PUBLICATION_PREREQUISITES` |
| `05c486674378f1c8807375905ba1eedb84dd1b31` | 003F canonicalization implementation | Three governance artifacts: Brief, machine-readable provenance, companion work order |
| `34fb7306378395cd6f9ef1aa83343ec79d9c4404` | 003F provenance governance closure | One dated 003F task report |
| `72101002e18f6ba770ab53d02b6f9c0e4cf3f201` | B2 authority implementation evidence | `lifecycle_formal_publication.py` and its focused test |
| `d41985ae7027d7fd5d4f995544f5f80d9b70e1b3` | B2 authority governance evidence | Project-memory governance records and the B2 authority reconciliation report |

Ancestry checks passed: `a8357d4` is an ancestor of `05c4866` and `7210100`;
`05c4866` is an ancestor of `34fb730`; and `7210100` is an ancestor of
`d41985a`. The 003F source task therefore remains a historical, recoverable
branch lineage, while this task registers it against the current GOV-003
development line. Historical work is not marked integrated merely because its
objects are registered.

## Exact artifact registration

The durable registration is
`docs/governance/provenance/TASK-TOPIC-B2-003F-CANONICAL-PROVENANCE-001.json`.
It intentionally records provenance and qualification rather than duplicating
the primary Brief.

### 003F primary and companion artifacts

| Artifact | Bytes | SHA-256 | Treatment |
| --- | ---: | --- | --- |
| C: owner source Brief | 6,931 | `c304032f41bca466b70c5f1919f239b52030e6f1d5d284506c63623f649aaddf` | Source hash preserved |
| Historical canonical Brief | 6,930 | `77319ae5fd51470265dd0030f38a5cc9b18ae0214d01a0a508c2b32025b8c8a9` | UTF-8/LF with one terminal newline; source differs only by one terminal blank line |
| Companion work order | 3,777 | `b901947aa3c3eaecdf58e3ed055a2efe1bd18c5934198821363a8fc883e41f4a` | Byte-preserving |

The Brief normalization was checked by comparing the source after removing
terminal newline repetition and adding one terminal newline to the historical
canonical bytes. The normalized bytes match exactly. The source and canonical
hashes remain separately recorded; they are not incorrectly presented as
byte-identical.

The authority qualification remains:

```text
ARTIFACT_VERSION=PHASE-3.7 / NEXT-V2
STATUS=FORMULA/POLICY APPROVED - ACTIVATION BLOCKED
MANUAL_TOPIC_AUTHORITY=VERIFIED_AT_ARTIFACT_LEVEL
FORMAL_POLICY_APPROVAL_RECORD=NOT_PRESENT
```

The Markdown Brief is not the strict 003G/003H-compatible JSON approval record
required by the runtime approval guard. No missing owner, effective-date,
rollback, approver, digest-binding, or Eligibility Audit values were invented.

### B2 authority bindings and cardinality

| Authority artifact | Embedded artifact SHA | Source master SHA | Verified cardinality |
| --- | --- | --- | --- |
| `config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json` | `1100c8bb4f760f6edab6e2ed59f4ee1d3e4776777b63a494d2611990f8c31753` | `8f5646f4b9e5f00c9263bf7511911f4520ec2b940af1fc50c778b0d9e83ce2c4` | 107 leaves, 25 parents, 132 raw topic entries |
| `config/topic_structural_role_authority/structural-role-authority-20260912.v4.json` | `c35c15911c355766dbaa53e76629ae17c84f8d1bbc98e2053b7e87592c0274bc` | `641a1c1dbd1849d70ffd7efa775f24d0bc5f7e35610179e27f0a587834bce188` | 1,160 rows, 107 distinct leaves |

Structural-role distributions are 474 `PRIMARY` / 686 `SECONDARY` and 650
`CORE` / 329 `REPRESENTATIVE` / 181 `RELATED`; every row is `APPROVED`.
The embedded artifact hashes were recomputed using the repository builder
semantics: canonical JSON SHA-256 after excluding the self-referential
`artifactSha256` field. Raw file hashes are not substituted for those embedded
values.

The existing evidence still reports a database readback gap of 106 active
leaves and 24 active parents against required 107/25. This task did not repair,
reclassify, or reinterpret that readback.

## Lifecycle reconciliation

Current GOV-003 Project Memory was missing current manifests for the historical
B2 authority reconciliation and 003F provenance tasks. The existing B2 gate
manifest was present but still `PLANNED`. This task added only the missing
current-lineage registrations and reconciled the existing gate:

| Task ID | Before current-lineage record | After registration | Meaning |
| --- | --- | --- | --- |
| `TOPIC-B2-AUTHORITY-RECONCILIATION-001` | Manifest absent; historical report/SHAs existed | `PARTIAL` | Historical authority work is recoverable; formal publication remains unresolved |
| `TOPIC-B2-CANONICAL-ARTIFACT-PROVENANCE-AND-PUBLICATION-GATE-001` | `PLANNED` | `BLOCKED` | Historical gate evidence explicitly blocks on formal publication prerequisites |
| `TASK-TOPIC-B2-003F-CANONICAL-PROVENANCE-001` | Manifest absent; historical task report was bounded `COMPLETE` | `READY_FOR_INTEGRATION` | Exact implementation/governance SHAs are registered; it is not `INTEGRATED` |
| `TASK-INT-TOPIC-B2-003F-GOVERNED-REGISTRATION-001` | New task record | `PARTIAL` | Registration boundary is complete; product integration/publication is intentionally outside scope |

Legal lifecycle checks passed for the required bounded paths:

```text
PLANNED -> IN_PROGRESS
IN_PROGRESS -> READY_FOR_INTEGRATION
IN_PROGRESS -> PARTIAL
PLANNED -> BLOCKED
```

The final statuses deliberately preserve the distinction between implemented,
registered, integrated, deployed, and verified. The 003F series is closed for
the bounded provenance/registration objective; this does not close formal B2
publication.

## Project Memory recovery test

A fresh-reader check was run against only the current E: manifests and the
current provenance registry, without relying on this conversation or the
historical worktree. It must recover:

```text
TASK_ID=TASK-TOPIC-B2-003F-CANONICAL-PROVENANCE-001
REGISTERED_BY=TASK-INT-TOPIC-B2-003F-GOVERNED-REGISTRATION-001
IMPLEMENTATION_SHA=05c486674378f1c8807375905ba1eedb84dd1b31
GOVERNANCE_SHA=34fb7306378395cd6f9ef1aa83343ec79d9c4404
PRIMARY_SOURCE_SHA=c304032f41bca466b70c5f1919f239b52030e6f1d5d284506c63623f649aaddf
PRIMARY_CANONICAL_SHA=77319ae5fd51470265dd0030f38a5cc9b18ae0214d01a0a508c2b32025b8c8a9
COMPANION_SHA=b901947aa3c3eaecdf58e3ed055a2efe1bd18c5934198821363a8fc883e41f4a
LIFECYCLE_ARTIFACT_SHA=1100c8bb4f760f6edab6e2ed59f4ee1d3e4776777b63a494d2611990f8c31753
STRUCTURAL_ROLE_ARTIFACT_SHA=c35c15911c355766dbaa53e76629ae17c84f8d1bbc98e2053b7e87592c0274bc
CARDINALITY=107_LEAVES/25_PARENTS/1160_ROLE_ROWS/107_DISTINCT_LEAVES
FORMAL_PUBLICATION=NOT_ACTIVE
FORMAL_DB_READBACK=PENDING_OPERATOR
A10_A9=WAITING
003G_003H=SEPARATE_WORKSTREAM
STOCK=WAITING
OPPORTUNITY=WAITING
NEXT_ACTION=OWNER_CONTROLLED_FUTURE_GATE; NOT_AUTO_STARTED
```

## Boundary and downstream reconciliation

- A10/A9 remains a separate active workstream with source/runtime alignment and
  operator/integration gates unresolved. No A10/A9 file or manifest was changed.
- 003G/003H remains a separate approval-provenance workstream. No 003G/003H
  artifact or report was changed.
- Formal B2 database readback remains `PENDING_OPERATOR`; no PostgreSQL access,
  taxonomy sync, or materialization was attempted.
- Stock remains waiting behind formal Topic/policy publication.
- Opportunity remains blocked pending formal Topic/policy publication.
- No `services/**`, `apps/**`, `packages/**`, `infra/**`, migration, frontend,
  live scheduler, publication, or `NEXT_TASK` surface was changed.

## Validation evidence

Current registration checks:

- Governance self-test: PASS.
- All current task manifests and referenced commits: PASS; 13 manifests validated.
- Current integration worktree branch, base ancestry, and state: PASS.
- Current integration ownership check, including worktree status: PASS.
- Lifecycle contract checks: PASS for all four legal transition paths listed above.
- Historical 003F manifest integration gate: READY; the current registration
  manifest integration gate is intentionally BLOCKED because this task has no
  product implementation commit and remains `PARTIAL` at the publication
  boundary. This is the expected governance-only result, not a failed 003F
  provenance registration.
- Source/canonical hashes, normalization, embedded authority hashes, cardinality,
  and structural distributions: PASS.
- Conflict-marker scan and `git diff --check`: required before final commit;
  no product-code lint or compile run is applicable to this documentation-only
  closeout.
- Historical 003F source report records 93 focused tests, Ruff, and compileall
  as passing for its own implementation. Those historical results are evidence,
  not a claim that this registration task changed or reran application code.
- Incomplete-work audit is read-only and preserves all unresolved artifacts;
  nothing was deleted or silently abandoned. The bounded audit reported 27
  fixture/synthetic candidates, 9 legacy/deprecated candidates, 2 orphan
  candidates, and 2 placeholder candidates (40 hits total); these were not
  altered.

## Final boundary

```text
RESULT=COMPLETE_FOR_BOUNDED_003F_GOVERNED_REGISTRATION
FORMAL_PUBLICATION=NOT_ACTIVE
FORMAL_DB_READBACK=PENDING_OPERATOR
C_DRIVE_TOUCHED=NO
PRODUCTION_TOUCHED=NO
PUSH=NO
NEXT_TASK=OWNER_CONTROLLED; NOT_AUTO_STARTED
```

The next formal publication decision remains owner-controlled and is not
started by this closeout.
