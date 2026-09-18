# Topic/B2 Layer 2 Formal Authority Contract

**Status:** `IMPLEMENTED / VALIDATED / FORMAL-POLICY-READY / PUBLICATION-GATED`

**Contract version:** `topic-layer2-formal-authority.v1`

**Task:** `TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001`

## Purpose and frozen boundary

This contract represents the already-approved Topic/B2 Layer 2 architecture. It
does not redesign the policy, select Leader Set members, approve Lifecycle
transition thresholds, activate a provider, or publish to Production.

Layer 2 has three distinct outputs:

1. Daily Strength — current/day-level topic strength;
2. Score/Grade — the existing deterministic 003F foundation; and
3. Five-Stage Lifecycle — an independent thematic lifecycle.

The invariant is:

```text
DAILY_STRENGTH != LIFECYCLE
```

The formal contract must preserve that distinction even when the historical
Score/Grade approval schema does not contain Lifecycle fields.

## Versioned identity

The Owner decision recovered from the prior governed closeout supplies the
conceptual identity `TOPIC_B2_LAYER2_POLICY_V1` and conceptual bundle
`topic-b2-layer2-policy-v1`. Repository-compatible resolution for this v1
contract is:

```text
policyBundleId      = topic-b2-layer2-policy
policyBundleVersion = topic-b2-layer2-policy-v1
candidateId         = TOPIC_B2_LAYER2_POLICY_V1
candidateVersion    = v1
effectiveDate       = 2026-09-15
```

These values identify the approved policy bundle. The continuation Owner
decision resolved the formal identity through the repository registry:

```text
ownerId          = topicpilot-owner
ownerKind        = GOVERNANCE_OWNER
ownerPrincipal   = GOVERNANCE_OWNER:topicpilot-owner
credential       = false
accountBinding   = none
```

The registry is `topicpilot_api.governance_identity`; it is provenance
metadata, not login authentication or RBAC. The exact approval timestamp is
still absent, so the formal record preserves a null timestamp rather than
inventing one.

## Schema strategy

The strategy is **composition with a new versioned envelope**:

```text
topic-layer2-formal-authority.v1
├── DailyStrengthContract
├── ScoreGradeContract
│   └── legacy topic-score-pm-approval.v1 reference
└── LifecycleContract
```

The legacy `topic-score-pm-approval.v1` record remains supported and retains
its original meaning: an opaque Score/Grade policy metadata gate. It is never
reinterpreted as full Layer 2 authority. A complete Layer 2 record is
distinguishable by the new schema version and explicit independent component
objects.

No migration, ORM table, API route, generated client, or persistence write was
required for this artifact contract. The authoritative artifact registration
is under the task report directory; database materialization is a separate
future operator-gated decision.

## Component contracts

### Daily Strength

The current approved status is:

```text
status: PARTIAL_BY_DESIGN
failClosed: true
```

The contract carries separate lists of `verifiedComponents`,
`unverifiedComponents`, and `parameterProvenance`. Unknown parameters are not
converted to defaults, zeroes, or inferred thresholds. A non-fail-closed
partial Daily Strength object is invalid.

### Score/Grade

`ScoreGradeContract` references the legacy schema and the reviewed 003F
approval artifact digest. It also records whether the legacy strict
`PolicyApprovalRecord` is `PENDING_RECORD` or `CREATED` and, when created, its
deterministic record digest.

This preserves the verified Score/Grade mechanics without claiming that a 003F
brief or research artifact is itself the strict PolicyApprovalRecord required
by the legacy guard.

### Lifecycle

The exact stages are:

```text
SPROUTING
FERMENTING
MAIN_RISE
MATURE
DECLINING
```

The contract requires explicit booleans proving independence from Daily
Strength and Score/Grade. Transition policy is represented separately from
stage identity. The current approved boundary is
`VERIFIED_COMPONENTS_ONLY` / `PARTIAL_BY_DESIGN` with `failClosed=true`; no
unrecovered transition threshold, hysteresis value, or duration is invented.

### Reviewed provenance

Every evidence reference contains an artifact identity/version, source
reference, scope, and optional SHA-256. Approved/verified evidence requires a
digest. `PARTIAL_PROVENANCE` and `UNVERIFIED_PARAMETERS` may omit a digest but
must remain visible and fail-closed through the component contract.

## Authority, publication, and activation states

The new envelope separates:

```text
authorityState:   POLICY_APPROVED | PRODUCTION_ACTIVE | BLOCKED
publicationState: UNPUBLISHED | READY | ACTIVE | BLOCKED
activationState:  NOT_ACTIVE | ACTIVE
```

The 003G-style validator only validates the authority envelope. It does not
grant approval and never permits this task to activate Production. 003H exposes
metadata such as `policyApproved`, `productionActive`, component statuses,
stages, and limitations without changing authority state.

An active publication requires an active activation state; an active activation
requires `PRODUCTION_ACTIVE`. The formal policy record is now
`POLICY_APPROVED`, while publication remains `BLOCKED` and activation remains
`NOT_ACTIVE`.

## Owner identity rule

`ownerIdentity` is nullable in the artifact model so the governed readback can
truthfully show why a record is blocked. The formal validator rejects null,
empty, display-name, test-fixture, email, account, or arbitrary alias values.
Accepted repository-native shapes are limited to a future registered
governance principal such as:

```text
OWNER:<stable-id>
GOVERNANCE_OWNER:<stable-id>
principal://<governance-domain>/<stable-id>
```

The registered principal `GOVERNANCE_OWNER:topicpilot-owner` is the only
resolved principal for this Owner decision. Legacy `PolicyApprovalRecord.owner`
stores the stable key `topicpilot-owner`; the Layer 2 envelope stores the
namespaced principal so the schema remains explicit about identity kind.
Unknown aliases and unregistered principals remain fail-closed.

## 003G and 003H

The new `evaluate_layer2_authority()` function is the Layer 2 003G-compatible
guard. It returns stable fail-closed reason codes, including:

- `FORMAL_OWNER_IDENTITY_REQUIRED`;
- `INVALID_OWNER_IDENTITY`;
- `UNKNOWN_POLICY_BUNDLE_ID` / `UNKNOWN_POLICY_BUNDLE_VERSION`;
- `INVALID_LIFECYCLE_STAGE`;
- `LAYER2_OUTPUTS_NOT_INDEPENDENT`;
- `DAILY_STRENGTH_NOT_FAIL_CLOSED`; and
- `LEGACY_SCORE_GRADE_RECORD_MISSING`.

`export_layer2_authority_artifact()` and
`parse_layer2_authority_artifact()` are the strict 003H artifact boundary.
They reject missing and unknown top-level and nested fields. The parser does
not apply approval semantics. `export_layer2_metadata()` is a readback-only
projection and cannot grant authority.

The authoritative continuation artifacts are:

- `governance-identity.json` — registered `topicpilot-owner` semantics;
- `score-grade-policy-approval-record.json` — legacy v1 Score/Grade subset;
- `layer2-policy-approval-record.json` — Layer 2 v1 formal envelope; and
- `layer2-policy-approval-metadata.json` — 003H metadata readback.

003G validation passes for both the legacy record and the Layer 2 envelope.
003H strict parse/round-trip and deterministic hashes pass. These artifacts do
not authorize Production activation.

## Closeout disposition

The schema, identity registry, compatibility implementation, formal
PolicyApprovalRecord, 003G guard, and 003H readback are complete and tested.
The Owner decision is preserved as a continuation after the prior
`FORMAL_OWNER_IDENTITY_DECISION_REQUIRED` stop; the earlier report remains
historically unchanged. Formal policy authority is `READY`, while formal
publication remains `BLOCKED` pending DB readback, Leader Set/Score runtime
gates, and the independently branch-only/operator-gated A10/A9 line.
