# CONTINUATION — TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001

## 1. Governed continuation identity

| Field | Result |
|---|---|
| Task | `TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001` |
| Mode | `ONE_SHOT_OWNER_IDENTITY_CONTINUATION_AND_CLOSEOUT` |
| Role | `SCHEMA_OWNER_AND_INTEGRATION_OWNER` |
| Worktree | `E:\TopicPilot\worktrees\schema-b2-layer2-formal-authority-001-20260915` |
| Branch | `codex/schema-b2-layer2-formal-authority-contract-001-20260915` |
| Starting closeout SHA | `56fdef52e7e280fb0d753f6e5f756f066a749845` |
| Governed development base | `a8357d46194f9669709f184949270e20a7a2546c` |
| Previous implementation SHA | `3011f00fe50e5c397635ef9a25ca3a9282bbd523` |
| Previous governance SHA | `ee65c530058da5694741e4e5d7c5dcc1895ba9b0` |
| C: | `UNTOUCHED` |
| Production | `UNTOUCHED` |
| Push / merge / deploy | `NO` |
| `NEXT_TASK` | `NOT MODIFIED` |

The previous report remains historical evidence and is not rewritten. It
closed at `FORMAL_OWNER_IDENTITY_DECISION_REQUIRED`. This continuation records
the new Owner decision and the subsequent formal-record work.

## 2. Owner identity decision and provenance

The Owner supplied the previously missing formal identity decision:

```text
identity_type=GOVERNANCE_OWNER
owner_id=topicpilot-owner
display_name=TopicPilot Owner
credential=false
account_binding=none
```

The stable key is `topicpilot-owner`; display name, workstation, agent,
account, email, and Git identity are not used as authority. The repository
registry is:

```text
services/api/src/topicpilot_api/governance_identity.py
schema=topicpilot-governance-identity.v1
principal=GOVERNANCE_OWNER:topicpilot-owner
authority=PRODUCT_POLICY_APPROVAL, FORMAL_GOVERNANCE_DECISION
```

The registry answers who the identity represents, what authority it carries,
that it is not a credential, and which formal decision it references. The
Layer 2 envelope records the namespaced principal; the legacy opaque
`PolicyApprovalRecord.owner` records the stable key `topicpilot-owner`.

The historical sequence is preserved:

```text
Owner Layer 2 policy decision
  -> formal authority contract engineering
  -> FORMAL_OWNER_IDENTITY_DECISION_REQUIRED
  -> Owner selects topicpilot-owner
  -> formal record continuation
```

## 3. Formal policy records

The Owner's existing decision is encoded without policy redesign:

```text
OWNER_POLICY_DECISION=APPROVE_EXISTING_LAYER2_POLICY_WITH_FAIL_CLOSED_ACTIVATION
OWNER_POLICY_REDESIGN_REQUIRED=NO
POLICY_BUNDLE_ID=topic-b2-layer2-policy
POLICY_BUNDLE_VERSION=topic-b2-layer2-policy-v1
CANDIDATE_ID=TOPIC_B2_LAYER2_POLICY_V1
CANDIDATE_VERSION=v1
EFFECTIVE_DATE=2026-09-15
```

### 3.1 Legacy Score/Grade subset

The strict legacy `topic-score-pm-approval.v1` record is now present at:

`TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001-20260915/score-grade-policy-approval-record.json`

It references the canonical 003F brief and preserves its verified mechanics:
breadth participation, leadership, normalization, weighted aggregation,
eligibility, and grade thresholds. The free-text limitations explicitly retain
the independent Lifecycle and partial Daily Strength boundaries.

```text
LEGACY_POLICY_RECORD=CREATED
LEGACY_POLICY_RECORD_SHA256=ed1fbd37ca3294566218c2712287cd623179453efcb352ab8b71ace8538c8c85
LEGACY_POLICY_GUARD=PASS
```

The existing v1 record remains a Score/Grade subset. It is not reinterpreted
as the full Layer 2 contract.

### 3.2 Layer 2 formal record

The strict Layer 2 record is:

`TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001-20260915/layer2-policy-approval-record.json`

```text
LAYER2_FORMAL_SCHEMA=topic-layer2-formal-authority.v1
LAYER2_POLICY_RECORD=CREATED
LAYER2_POLICY_RECORD_SHA256=7756221d9a0d2bc1641a2d800f7e1585a171f197877cc6beeb00b1a98c30def7
OWNER_PRINCIPAL=GOVERNANCE_OWNER:topicpilot-owner
AUTHORITY_STATE=POLICY_APPROVED
PUBLICATION_STATE=BLOCKED
ACTIVATION_STATE=NOT_ACTIVE
APPROVAL_TIMESTAMP=NULL_UNRECOVERED
```

The record preserves:

- Daily Strength `PARTIAL_BY_DESIGN`, fail-closed, with unresolved parameters
  visible rather than defaulted;
- Score/Grade `APPROVED_VERIFIED`, composed through the legacy record;
- independent Lifecycle `APPROVED` with exactly
  `SPROUTING, FERMENTING, MAIN_RISE, MATURE, DECLINING`;
- separate authority, publication, and activation states; and
- formal DB, Leader Set, A10/A9, and runtime limitations.

## 4. 003G and 003H results

```text
003G_VALIDATION=PASS
003G_SCOPE=legacy Score/Grade guard plus Layer 2 authority envelope
003G_GRANTS_APPROVAL=NO
003H_METADATA_READBACK=PASS
003H_STRICT_ROUND_TRIP=PASS
003H_METADATA_PATH=TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001-20260915/layer2-policy-approval-metadata.json
003H_METADATA_GRANTS_AUTHORITY=NO
```

The Layer 2 hash is generated from canonical sorted JSON with UTF-8 encoding,
stable separators, and no runtime timestamp. Repeated calculation and strict
parse/export round-trip produce the same digest. The legacy hash uses the same
deterministic serialization rule.

## 5. Current external gates

### Formal DB readback

The current repository evidence does not contain a newer verified
`TASK-TOPIC-B2-107-25-FORMAL-DB-READBACK-001` result. The latest B2
publication-gate evidence still reports the required 107 Leaf / 25 Parent
readback as blocked/not proven. Therefore:

```text
FORMAL_DB_107_25_1160_READBACK=PENDING / BLOCKED_OPERATOR
```

No DB access, taxonomy sync, migration, or protected readback was performed.

### A10/A9 and migration 0040

The latest verifiable A10/A9 recovery report is committed at
`78fe1b83c152c6f849659cab59f1a4ecd07e381e`. It reports the A10/A9 closure as
partial, branch-only, and operator-gated; the hardened writer/replay and
`0040` closure are not canonical Production evidence. A later unverified
prompt claim cannot override that repository evidence.

```text
A10_A9_ENGINEERING=PARTIAL / BRANCH_ONLY_CLOSURE / OPERATOR_GATED
MIGRATION_0040=UNTOUCHED / BRANCH_ONLY_COLLISION_PRESERVED
```

This task does not reopen or repair that workstream.

## 6. Downstream readiness

```text
FORMAL_POLICY_AUTHORITY=READY
B2_FORMAL_PUBLICATION_READINESS=PARTIAL / BLOCKED
B2_FORMAL_PUBLICATION_ACTIVE=NO
A9_FORMAL_WRITER_POLICY_PREREQUISITE=SATISFIED
A9_WRITER_ACTIVATION=NOT_AUTHORIZED / SEPARATE_GOVERNED_ACTION
OPPORTUNITY_B2_AUTHORITY_PREREQUISITE=PARTIAL
STOCK_B2_AUTHORITY_PREREQUISITE=PARTIAL
```

The policy prerequisite for A9 is satisfied by the validated formal record;
this does not authorize the A9 writer or any operator task. Opportunity and
Stock remain partial because they require genuine B2 publication/readback and
their own downstream contracts. No Opportunity, Stock, Today, frontend, or
Production code was changed.

## 7. Validation

| Check | Result |
|---|---|
| Owner identity registry resolution | `PASS` |
| Legacy PolicyApprovalRecord validation | `PASS` |
| Layer 2 003G validation | `PASS` |
| Layer 2 003H strict parse/round-trip | `PASS` |
| Legacy deterministic hash | `PASS`; `ed1fbd37ca3294566218c2712287cd623179453efcb352ab8b71ace8538c8c85` |
| Layer 2 deterministic hash | `PASS`; `7756221d9a0d2bc1641a2d800f7e1585a171f197877cc6beeb00b1a98c30def7` |
| Focused Layer 2/legacy/runtime suite | `56 passed` |
| Ruff | `PASS` |
| Ruff format | `PASS` |
| Python 3.12 compile | `PASS` |
| Broader known baseline failure | `1 pre-existing lifecycle encoding failure; task-caused 0` |
| Project Memory recovery | `PASS` |
| DB / Production / scheduler / deployment | `NOT PERFORMED` |

## 8. Project Memory recovery

Repository artifacts now answer:

1. Formal Owner identity is `topicpilot-owner`.
2. It is a stable non-credential `GOVERNANCE_OWNER` identity.
3. Layer 2 is `topic-layer2-formal-authority.v1`.
4. The Layer 2 PolicyApprovalRecord exists with SHA-256
   `7756221d9a0d2bc1641a2d800f7e1585a171f197877cc6beeb00b1a98c30def7`.
5. Daily Strength is `PARTIAL_BY_DESIGN` and fail-closed.
6. Score/Grade is approved/verified through legacy v1.
7. Lifecycle is independent and has five exact stages.
8. 003G and 003H both pass.
9. Formal policy authority is ready.
10. Formal publication is not active and remains gated by DB/runtime/operator
    evidence.
11. A10/A9 remains partial/branch-only/operator-gated in current evidence.
12. Opportunity and Stock remain downstream partial.

```text
PROJECT_MEMORY_RECOVERY_TEST=PASS
```

## 9. Exact SHAs and safety

```text
CURRENT_GOVERNED_BASE_SHA=a8357d46194f9669709f184949270e20a7a2546c
TASK_EXECUTION_BASE_SHA=a8357d46194f9669709f184949270e20a7a2546c
IMPLEMENTATION_SHA=1a49787fbd10410333772e218601050186270c72
SCHEMA_SHA=a5e1ec615017d2a2ece2a7ccf47b771afa8560bf3ca554b73cc3c39aef6f84e0
IDENTITY_REGISTRY_SHA=75eddd4223d70d0fb8297efb204ea483e2d07c4a61a936d2a9361f3655bc6bae
IDENTITY_ARTIFACT_SHA256=aac36f3a5329d4c2dd247997aee2ce0f6109b1fb9583619bcb622f3b87fb243c
GOVERNANCE_SHA=06c68361eac8ad291736aafcf7bf7ec4f099d2aa
FINAL_CLOSEOUT_SHA=REPORTED_IN_FINAL_CLOSEOUT
REPORT_SHA256=REPORTED_IN_FINAL_CLOSEOUT
POLICY_RECORD_SHA256=ed1fbd37ca3294566218c2712287cd623179453efcb352ab8b71ace8538c8c85
LAYER2_POLICY_RECORD_SHA256=7756221d9a0d2bc1641a2d800f7e1585a171f197877cc6beeb00b1a98c30def7
C_DRIVE=UNTOUCHED
PRODUCTION=UNTOUCHED
PRODUCTION_MUTATION=NONE
MIGRATION_0040=UNTOUCHED
PUSH=NO
MERGE_MAIN=NO
DEPLOY=NO
NEXT_TASK_CHANGED=NO
```

## 10. Closeout

The formal Owner identity decision is resolved. Layer 2 formal policy
engineering and validation are complete. The remaining action is an
operator/protected readback and downstream integration decision; it is not
started automatically.

```text
NEXT_GOVERNED_ACTION=PROTECTED_FORMAL_DB_READBACK_AND_SEPARATE_A10_A9_INTEGRATION_GATE
OWNER_DECISION_REQUIRED=NO
```
