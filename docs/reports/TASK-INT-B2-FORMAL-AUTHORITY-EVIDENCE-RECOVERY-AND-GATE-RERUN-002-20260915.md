# TASK-INT-B2-FORMAL-AUTHORITY-EVIDENCE-RECOVERY-AND-GATE-RERUN-002

Date: 2026-09-15
Role: INTEGRATION_OWNER
Mode: ONE_SHOT_AUTHORITATIVE_EVIDENCE_RECOVERY_CANONICAL_REGISTRATION_AND_GATE_RERUN
Result: COMPLETE_WITH_EXTERNAL_GATE
Stop reason: UNRESOLVED_0040_CANONICAL_PROVENANCE_DECISION

## 1. Executive Summary

This run recovered and boundedly registered two previously unreachable evidence
surfaces:

1. Layer 2 formal-authority implementation, Owner identity registry, legacy
   Score/Grade record, Layer 2 PolicyApprovalRecord, metadata, tests, and
   continuation closeout.
2. The complete read-only Production DB continuation bundle proving the 0040
   revision, 107 Leaves, 25 Parents, 107 hierarchy edges, 1,160 approved
   structural-role rows, and exact authority-content matches.

The supplied Layer 2 implementation and governance identifiers were not exact
Git objects. The exact source objects are recorded in sections 5 and 11.
The supplied final closeout object is exact and was recovered.

The claimed 0040 resolved closure was not recoverable. The repository still
contains two branch-only, byte-distinct but AST-equivalent 0040 candidates and
no recoverable Schema Owner content/provenance decision or claimed
b518/587/93f commits. That is the remaining external gate.

No migration, Production write, publication activation, deploy, push, Today
change, Opportunity change, Stock change, or C: checkout mutation occurred.

## 2. Previous False/Stale Blockers

The prior PARTIAL / UNRECOVERABLE_REQUIRED_EVIDENCE result was accurate for
the evidence reachable at that time. It was not proof that parallel work had
never completed.

| Prior field | Reconciled truth |
|---|---|
| FORMAL_OWNER_IDENTITY=BLOCKED | Resolved by committed GOVERNANCE_OWNER:topicpilot-owner registry |
| POLICY_APPROVAL_RECORD=BLOCKED | Legacy and Layer 2 records are present and hash-verified |
| 003G/003H | PASS / PASS |
| DB 107/25/107/1160 | Verified by the read-only Production continuation |
| 0040/A10-A9 | Not resolved; prior collision report remains authoritative |
| Leader Set | Still not formal |
| Publication | Still separately gated |

Attachment prompts were treated as claims only. Repository objects and recovered
evidence files took precedence.

## 3. Current Canonical Baseline

- Canonical C checkout: C:\Users\acer\Desktop\題材領航\topicpilot-platform
- C HEAD before and after: 02d3086183d1c582bb6c66c4c316340ccce3fa97.
- C dirty status count before and after: 152.
- Current integration starting point: 48f80c5cc154ae2620b40766351abc9094cbef35.
- Governed development common base: a8357d46194f9669709f184949270e20a7a2546c.
- Isolated worktree: E:\topicpilot-worktrees\int-b2-formal-authority-evidence-recovery-and-gate-rerun-002-20260915.
- Branch: codex/task-int-b2-formal-authority-evidence-recovery-and-gate-rerun-002-20260915.

## 4. Evidence Recovery Map

| Surface | Source and verification | Disposition |
|---|---|---|
| Layer 2 | Clean Schema Owner source branch; exact commits and artifacts inspected | BOUNDED_PORT and CANONICALIZED |
| Layer 2 records | Strict artifact, identity, policy, and digest checks | CANONICALIZED |
| DB readback | Continuation report, JSON, SQL, and manifest source hashes verified | REGISTERED READ-ONLY EVIDENCE |
| 0040 | Canonical refs, remote refs, worktrees, and attachments searched | HISTORICAL/CONFLICTING; decision required |
| 003F | Existing canonical exact artifact and governance refs | ALREADY_CANONICAL |

## 5. Layer 2 Authority Recovery

Schema: topic-layer2-formal-authority.v1.

The contract composes Daily Strength, Score/Grade, and independent Lifecycle:

- Daily Strength: PARTIAL_BY_DESIGN and fail-closed.
- Score/Grade: APPROVED_VERIFIED through legacy topic-score-pm-approval.v1.
- Lifecycle: APPROVED, independent, fail-closed, exactly SPROUTING,
  FERMENTING, MAIN_RISE, MATURE, DECLINING.

The formal record separates authority, publication, and activation:

- authority: POLICY_APPROVED;
- publication: BLOCKED;
- activation: NOT_ACTIVE.

Verified digests:

- schema: a5e1ec615017d2a2ece2a7ccf47b771afa8560bf3ca554b73cc3c39aef6f84e0;
- legacy PolicyApprovalRecord: ed1fbd37ca3294566218c2712287cd623179453efcb352ab8b71ace8538c8c85;
- Layer 2 PolicyApprovalRecord: 7756221d9a0d2bc1641a2d800f7e1585a171f197877cc6beeb00b1a98c30def7;
- identity artifact: aac36f3a5329d4c2dd247997aee2ce0f6109b1fb9583619bcb622f3b87fb243c;
- identity registry: 75eddd4223d70d0fb8297efb204ea483e2d07c4a61a936d2a9361f3655bc6bae.

## 6. Owner Identity Recovery

The recovered stable identity is GOVERNANCE_OWNER:topicpilot-owner.

The legacy record uses the stable key topicpilot-owner. The registry is
non-credential, has no account binding, and authorizes PRODUCT_POLICY_APPROVAL
and FORMAL_GOVERNANCE_DECISION. Display name, workstation, agent, email, and
Git identity are not authority.

## 7. PolicyApprovalRecord Recovery

Both records are present:

- strict legacy Score/Grade record: CREATED, digest verified;
- strict Layer 2 record: CREATED, digest verified.

The Owner decision is preserved as
APPROVE_EXISTING_LAYER2_POLICY_WITH_FAIL_CLOSED_ACTIVATION. This task did not
redesign or re-approve policy. The record's approvalTimestamp remains
null/unrecovered; its policy state remains POLICY_APPROVED.

## 8. 003F / 003G / 003H

003F remains verified:

- implementation: 05c486674378f1c8807375905ba1eedb84dd1b31;
- governance: 34fb7306378395cd6f9ef1aa83343ec79d9c4404;
- source authority: 107 Leaves / 25 Parents;
- structural-role authority: 1,160 approved rows.

Layer 2 003G validation: PASS.
Layer 2 003H strict metadata parse/round-trip: PASS.
Legacy compatibility: PASS.
Neither guard grants Production approval or activation.

## 9. Formal DB 107 / 25 / 107 / 1,160

The recovered continuation is a complete read-only operator result at
2026-09-15T12:33:14.768+08:00 Asia/Taipei.

- service runtime SHA: bf68cc8bf0a4432d7623db43f42e9219c94d7b6b;
- DB revision: 0040_task_a10_recovery_checkpoint_observability;
- active topics: 107 Leaves, 25 Parents, 132 unique topics;
- hierarchy: 107 date-effective edges, exact identity, no duplicate/invalid/orphan edges;
- structural roles: 1,160 rows, all approved, exact authority/source linkage;
- role content: exact match;
- role distribution: PRIMARY 474, SECONDARY 686, CORE 650,
  REPRESENTATIVE 329, RELATED 181;
- authority activation: ACTIVE v2 with 25 Parents / 107 Leaves / 107 lifecycle scope.

Normalized hashes:

- topic identity: 06CB9DB776682B65BB68B9F97DA6272557B65E772E5F2400DEDF779026B2BC13;
- hierarchy: 40EEAFFA1BDA80873EEEFDA9BF0654222CCCA041A0B0C85AFC00C4EADE34BD34;
- role content MD5: 6d2e7f0284060a439b6cb15163244630.

The source continuation manifest itself hashes to
992B8F676C19519B443B3BCDD870AFF577D54E72B302D174B5B1CA73588FFA2F.
The registered evidence directory contains the continuation report, SQL,
production JSON, and manifest. The committed mirror is line-ending-normalized;
the source hashes above remain the cryptographic authority and were verified
before registration.

No DML, DDL, migration, bootstrap, publication, deploy, scheduler, or
configuration operation was performed.

## 10. 0040 / A10-A9 Recovery

Recoverable 0040 candidates:

| Candidate | Commit | Blob | Content SHA-256 |
|---|---|---|---|
| A10 | 51dbe48db203adb56e5fbc47da2f44b0e33997d2 | 20b5947c4e8441468e78f4adc46de59c892b2c5d | fa435d2dc1e632a0b11e454484adb6f59fa49b0d273845e315500a45ec2d063e |
| Today | c544e2a5a6e3531232fb69e7580c99a0b1a5eef5 | c715d19aab1f4cf1a061745807b7c4411c303991 | c89647ee3cb593a52caec8c1af97142941f3377b2a484d41c724446d71968da1 |

They are byte-distinct but AST-equivalent. Neither has recoverable canonical
Schema Owner provenance. Claimed b5188c..., 587ca49..., and 93f6ce... objects
are absent. Therefore:

- 0040 collision: UNRESOLVED;
- Production exact-content provenance: UNPROVEN;
- A10 13:35: COMPLETE at branch-evidence boundary;
- A10 post-close: IMPLEMENTED_NOT_INTEGRATED / PARTIAL;
- A10/A9 governed lineage: PARTIAL.

No collision was recreated, renamed, reserved, or executed.

## 11. Canonical Registration

Recovered Layer 2 source commits:

- 3011f00fe50e5c397635ef9a25ca3a9282bbd523 — predecessor contract implementation;
- ee65c530058da5694741e4e5d7c5dcc1895ba9b0 — governance registration;
- 56fdef52e7e280fb0d753f6e5f756f066a749845 — documentation closeout;
- 1a4978700391df3e99ebbef263dd1bfe7af35c25 — Owner/policy resolution implementation;
- 06c6836f5acd1f665d8e2927ac6eb64cabdc01f7 — formal policy governance;
- e0a6eb34139116ebf4d4a0f4d218a799832ea523 — final continuation closeout.

The brief's 1a49787fbd... and 06c68361e... values were not the exact source
objects found. The exact objects above are used.

Canonical replay commits:

- b31a0f09788609644844883bc6fd7a057716c538;
- d1a822c36ed8a04b863950f7c75fbbabb55aa9ff;
- c882842415cb292b747f7008628cf728466bc5f3;
- 17bb8db30ffb69fcaca2f41997dc42a71d1634cc;
- abd2866a24a6b9ec1c24c70a9a6f3527911023d5;
- a734ae1ef959cb032c0e6c3b185a40b4a1b4e7ae.

The replay is bounded to the Layer 2 contract, tests, architecture record,
formal records, governance registration, and closeout. No unrelated branch
was merged.

## 12. Daily Strength

PARTIAL_BY_DESIGN is an approved contract state, not an automatic failure.
Verified components may emit authoritative values; unresolved parameters remain
null/unavailable and fail closed. It does not block independent Score/Grade or
Lifecycle policy authority.

## 13. Score / Grade

Score/Grade authority is APPROVED_VERIFIED at policy-record level. Formal
Score/Grade publication remains separately gated by approved Leader Set
projection, snapshot lineage, as-of/correction evidence, and runtime gates.

## 14. Lifecycle

Policy authority is APPROVED and independent with five stages.

- calculation: formal V1.3 evaluator exists;
- writer: formal lifecycle publisher exists with persist/dry-run boundary;
- storage: topic_lifecycle_formal_results ORM and migration contract exist;
- readback: formal result/read-model boundary exists;
- publication: NOT ACTIVE / FAIL-CLOSED because upstream lineage, complete
  coverage, transition provenance, and operator gates are not closed.

No lifecycle publication or Production write occurred.

## 15. Structural Role

The structural-role artifact and DB readback are authoritative for 1,160
approved role rows and exact source linkage. They do not create a formal
Leader Set. GovernedLeaderSet remains an explicit input contract with no
approved member/version/effective-date artifact.

## 16. 92 Snapshot Analysis

The 92 figure is the count of complete formal/published topic-level snapshot
rows available in each audited session; six sessions yielded 552 rows. It is
not the 107-topic authority denominator, a relation count, or a Leader Set.

The recovered continuation reconciles the scope as:
92 complete available observations + 15 unavailable/incomplete leaves = 107.

The 15 are availability/incompleteness cases, not a 20MA, liquidity, ranking,
or Leader Set filter. The sanitized operator bundle does not include their
identity list, so this report does not invent names. The 92 is an observed
complete subset, not a stable policy-defined eligible universe. A9 must remain
fail-closed for unavailable rows.

## 17. Leader Set

- implementation shape: explicit GovernedLeaderSet consumer contract;
- source: no approved formal Leader Set artifact;
- version/provenance/effective date: absent;
- structural-role artifact: not equivalent to Leader Set;
- publication support: blocked.

No proxy or synthetic strongest-observed set was promoted.

## 18. Lifecycle Writer / Publication Support

Calculation, formal writer, ORM storage, and formal read boundary are present
and tested. Activation/publication remains closed because formal input lineage
and complete scope coverage are not all satisfied. This is implementation
support, not Production publication authority.

## 19. A9 Gate Rerun

| Prerequisite | Result | Reason |
|---|---|---|
| Policy | SATISFIED | Layer 2 record verified |
| DB | SATISFIED | 107/25/107/1,160 readback verified |
| Structural Role | SATISFIED | Exact approved role authority |
| Leader Set | BLOCKED | No formal artifact/version/effective binding |
| Lifecycle | PARTIAL / BLOCKED | Policy approved; formal lineage/publication not closed |
| Runtime | BLOCKED | Separate writer activation gate |
| 0040 | BLOCKED | Collision/content provenance unresolved |
| A9 formal writer | BLOCKED | Remaining gates above |

Stale policy and DB blockers were removed.

## 20. Opportunity Gate Rerun

B2 policy is SATISFIED. Topic authority DB evidence is verified, but the
Opportunity downstream DB contract is only PARTIAL. A9, Lifecycle, Leader Set,
formal provider, and freshness remain BLOCKED/PARTIAL. Downstream readiness is
BLOCKED. No recommendation or provider activation occurred.

## 21. Stock Gate Rerun

B2 policy is SATISFIED at the Layer 2 record boundary. Topic DB authority is
verified, but Stock's full downstream contract is not independently closed.
Selector, news/notes, peer authority, formal Lifecycle, formal Score/Grade,
formal Leader Set, runtime, and readback remain blockers. Stock backend is
BLOCKED. No Stock frontend or backend work started.

## 22. Project Memory Root Cause

The gap was a topology/indexing failure:

- Layer 2 lived in a separate linked worktree/repository lineage.
- DB continuation evidence lived as an untracked task-local bundle.
- The Layer 2 continuation report carried stale prompt-style SHA fields.
- 0040 resolved identifiers existed only as claims, without objects or a
  completion report.
- The prior integration search did not index parallel task-local evidence into
  canonical docs/provenance.

## 23. Governance Repair

This task adds a current integration manifest, provenance record, report, source
to canonical replay mapping, and registered evidence mirror with source hashes.
No new governance framework or central Today/project-memory rewrite was created.

Recovery test: a fresh task from 48f80c5... can discover Layer 2 records, Owner
identity, DB continuation, source hashes, replay mapping, and the exact 0040
stop condition from the report and its manifest/provenance files.

## 24. Tests

- Canonical Layer 2 / legacy policy focused rerun: 32 passed in 2.84s.
- Structural-role, Score projection, Lifecycle contract, and formal Lifecycle
  rerun: 50 passed, 1 failed in 7.26s; the one failure is the registered
  lifecycle encoding baseline failure
  test_topic_lifecycle_contract_closure.py::test_frozen_stage_contract_has_one_owner_sequence_and_no_legacy_stage.
- Ruff on recovered Layer 2 code/tests: PASS; Python 3.12 compile: PASS.
- DB continuation read-only evidence, SQL set, and source manifest hash verified.
- 0040 candidate parsing and AST/byte collision audit retained.
- No migration, database mutation, deployment, publication, or scheduler test.
- diff-check: PASS; conflict-marker scan: PASS; manifest/lifecycle/worktree/
  ownership validation: PASS. The integration gate is BLOCKED as expected
  because the task remains PARTIAL and requires the 0040 owner decision.
- Task-caused failures: 0.
- Registered baseline failure: existing lifecycle encoding failure.
- Unknown failures: 0.

## 25. Remaining Blockers

B2: formal Leader Set artifact; formal Lifecycle upstream/transition/readback
closure; 0040 canonical decision; protected runtime gate.

A9: Leader Set; Lifecycle; 0040; runtime activation.

Opportunity: A9; formal provider; freshness; downstream contract.

Stock: selector; news/notes; peer; Lifecycle; Score/Grade; Leader Set and
downstream runtime/readback.

## 26. Next Governed Action

Schema Owner records canonical 0040 source/content/provenance without executing a
migration. Integration Owner then reruns 0040/A9/B2 release and publication
gates. A separate authority task must provide a formal Leader Set artifact and
complete Lifecycle upstream publication lineage. Production publication and
A9 writer activation remain fail-closed.

## Final YAML packet

TASK: TASK-INT-B2-FORMAL-AUTHORITY-EVIDENCE-RECOVERY-AND-GATE-RERUN-002
ROLE: INTEGRATION_OWNER
MODE: ONE_SHOT_AUTHORITATIVE_EVIDENCE_RECOVERY_CANONICAL_REGISTRATION_AND_GATE_RERUN
RESULT: COMPLETE_WITH_EXTERNAL_GATE
STOP_REASON: UNRESOLVED_0040_CANONICAL_PROVENANCE_DECISION
PREVIOUS_CANONICAL_BASE_SHA: 48f80c5cc154ae2620b40766351abc9094cbef35
CURRENT_CANONICAL_HEAD_BEFORE_TASK: 48f80c5cc154ae2620b40766351abc9094cbef35
CURRENT_GOVERNED_BASE: a8357d46194f9669709f184949270e20a7a2546c
TASK_EXECUTION_BASE_SHA: 48f80c5cc154ae2620b40766351abc9094cbef35
LAYER2_EVIDENCE_RECOVERY: VERIFIED_AND_CANONICALIZED
FORMAL_OWNER_IDENTITY: VERIFIED
FORMAL_OWNER_ID: topicpilot-owner
POLICY_APPROVAL_RECORD: CREATED_AND_VERIFIED
POLICY_RECORD_SHA256: ed1fbd37ca3294566218c2712287cd623179453efcb352ab8b71ace8538c8c85
LAYER2_POLICY_RECORD_SHA256: 7756221d9a0d2bc1641a2d800f7e1585a171f197877cc6beeb00b1a98c30def7
003F_GOVERNED_AUTHORITY: VERIFIED
003G_VALIDATION: PASS
003H_METADATA_READBACK: PASS
DAILY_STRENGTH: PARTIAL_BY_DESIGN
DAILY_STRENGTH_FAIL_CLOSED: YES
SCORE_GRADE_AUTHORITY: APPROVED_VERIFIED
LIFECYCLE_POLICY_AUTHORITY: APPROVED_INDEPENDENT_FIVE_STAGE
LIFECYCLE_WRITER_SUPPORT: IMPLEMENTED_NOT_ACTIVATED
LIFECYCLE_PUBLICATION_SUPPORT: BLOCKED_FAIL_CLOSED
FORMAL_DB_TOPIC_LEAVES: 107
FORMAL_DB_TOPIC_PARENTS: 25
FORMAL_DB_HIERARCHY_EDGES: 107
FORMAL_DB_STRUCTURAL_ROLE_ROWS: 1160
FORMAL_DB_CONTENT: VERIFIED_EXACT_PROVENANCE_MATCH
B2_DB_PREREQUISITE: SATISFIED
MIGRATION_0040_PROVENANCE: UNRESOLVED
MIGRATION_0040_COLLISION: UNRESOLVED
A10_1335: COMPLETE_BRANCH_EVIDENCE
A10_POST_CLOSE: PARTIAL_IMPLEMENTED_NOT_INTEGRATED
A10_A9_ENGINEERING: PARTIAL
FORMAL_SNAPSHOT_ROWS: 92_PER_SESSION_552_ACROSS_SIX_AUDITED_SESSIONS
FORMAL_SNAPSHOT_92_EXPLANATION: 92_COMPLETE_AVAILABLE_PLUS_15_UNAVAILABLE_EQUALS_107; NOT_DENOMINATOR; EXACT_15_IDS_NOT_IN_SANITIZED_BUNDLE
LEADER_SET_AUTHORITY: BLOCKED_NOT_FORMAL
LEADER_SET_PROVENANCE: NONE_APPROVED
B2_ENGINEERING_READY: YES_AUTHORITY_CONTRACT_AND_DB_EVIDENCE
B2_FORMAL_PUBLICATION_READINESS: BLOCKED
B2_FORMAL_PUBLICATION_ACTIVE: NO
A9_POLICY_PREREQUISITE: SATISFIED
A9_DB_PREREQUISITE: SATISFIED
A9_LEADER_SET_PREREQUISITE: BLOCKED
A9_LIFECYCLE_PREREQUISITE: PARTIAL_BLOCKED
A9_RUNTIME_PREREQUISITE: BLOCKED
A9_FORMAL_WRITER_READINESS: BLOCKED
OPPORTUNITY_B2_POLICY_PREREQUISITE: SATISFIED
OPPORTUNITY_B2_DB_PREREQUISITE: PARTIAL_DOWNSTREAM_CONTRACT
OPPORTUNITY_A9_PREREQUISITE: BLOCKED
OPPORTUNITY_FORMAL_PROVIDER_PREREQUISITE: BLOCKED
OPPORTUNITY_FRESHNESS_PREREQUISITE: PARTIAL_BLOCKED
OPPORTUNITY_DOWNSTREAM_READINESS: BLOCKED
STOCK_B2_AUTHORITY_PREREQUISITE: SATISFIED_POLICY_ONLY
STOCK_BACKEND_READINESS: BLOCKED
PROJECT_MEMORY_GAP_ROOT_CAUSE: UNREGISTERED_PARALLEL_WORKTREE_AND_TASK_LOCAL_EVIDENCE_PLUS_STALE_SHA_FIELDS
PROJECT_MEMORY_REPAIR: CANONICAL_REPORT_MANIFEST_PROVENANCE_EVIDENCE_MIRROR_AND_SOURCE_TO_CANONICAL_MAPPING
PROJECT_MEMORY_RECOVERY_TEST: PASS
TASK_CAUSED_FAILURES: 0
REGISTERED_BASELINE_FAILURES: 1_LIFECYCLE_ENCODING_FAILURE
UNKNOWN_FAILURES: 0
CANONICAL_INTEGRATION_SHA: SEE_FINAL_CLOSEOUT_COMMIT
GOVERNANCE_SHA: SEE_FINAL_CLOSEOUT_COMMIT
FINAL_CLOSEOUT_SHA: SEE_FINAL_CLOSEOUT_COMMIT
C_DRIVE: UNTOUCHED
PRODUCTION: UNTOUCHED
PRODUCTION_MUTATION: NONE
MIGRATION_EXECUTION: NOT_PERFORMED
PUSH: NO
OWNER_DECISION_REQUIRED: YES_FOR_0040
INTEGRATION_OWNER_ACTION_REQUIRED: NO_SAFE_ACTION_REMAINS_BEYOND_SCHEMA_OWNER_0040_DECISION
REMAINING_B2_BLOCKERS: LEADER_SET;LIFECYCLE_FORMAL_LINEAGE;0040_PROVENANCE;RUNTIME_GATE
REMAINING_A9_BLOCKERS: LEADER_SET;LIFECYCLE;0040;RUNTIME
REMAINING_OPPORTUNITY_BLOCKERS: A9;FORMAL_PROVIDER;FRESHNESS;DOWNSTREAM_CONTRACT
REMAINING_STOCK_BLOCKERS: SELECTOR;NEWS_NOTES;PEER;LIFECYCLE;SCORE_GRADE;LEADER_SET
NEXT_GOVERNED_ACTION: SCHEMA_OWNER_CANONICAL_0040_PROVENANCE_DECISION_THEN_INTEGRATION_GATE_RERUN
RECOMMENDED_NEXT_TASK: TASK-SCHEMA-0040-CANONICAL-PROVENANCE-RESOLUTION-001
RECOMMENDED_NEXT_OWNER: SCHEMA_OWNER

B2 FORMAL POLICY AUTHORITY: READY
B2 FORMAL DB 107/25/1160: VERIFIED
0040 / A10 ENGINEERING: EXTERNAL GATE - 0040 UNRESOLVED
LEADER SET: BLOCKED
LIFECYCLE PUBLICATION: BLOCKED_FAIL_CLOSED
A9 FORMAL WRITER: BLOCKED
B2 FORMAL PUBLICATION: BLOCKED
OPPORTUNITY: BLOCKED
STOCK: BLOCKED
PROJECT MEMORY: REPAIRED
