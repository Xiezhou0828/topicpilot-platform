# TASK-TOPIC-B2-107-25-FORMAL-DB-READBACK-001 — Continuation

## 1. Task and mode

Continuation of the existing governed task; no replacement archaeology task was created.

```text
MODE = ONE_SHOT_OPERATOR_READBACK_CONTINUATION
READ_AUTHORITY = YES
WRITE_AUTHORITY = NO
READBACK_TIMESTAMP = 2026-09-15T12:33:14.768+08:00 Asia/Taipei
```
## 2. Result

`COMPLETE` for the Production formal DB/read-model verification. The B2 DB prerequisite is satisfied. Formal publication, policy approval, A9 writer activation, Opportunity, and Stock remain separately governed.

## 3. Approved access path

Render dashboard authentication was already available. The official Render service is `topicpilot-api` at `https://topicpilot-api.onrender.com`; `/healthz` and `/readyz` returned HTTP 200 with runtime SHA `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b`. The official Neon console was authenticated and the `topicpilot` Production branch / `neondb` database was used through SQL Editor.

## 4. Read-only safety

Only SELECT statements were executed. No INSERT, UPDATE, DELETE, DDL, migration, rollback, bootstrap, activation, publication, deployment, scheduler change, or configuration change was performed. Two exploratory SELECTs failed closed because of schema/function differences; neither changed data.

## 5. Production migration revision

Direct readback from `public.alembic_version` returned:

```text
0040_task_a10_recovery_checkpoint_observability
```
This is the exact current Production DB revision; it was not inferred from a report and no migration was run.

## 6. Database and schema

```text
ENGINE = PostgreSQL
PROJECT = topicpilot
BRANCH = production
DATABASE = neondb
SCHEMA = topicpilot
```

## 7. 003F provenance

003F registration is verified. Implementation SHA: `05c486674378f1c8807375905ba1eedb84dd1b31`. Governance SHA: `34fb7306378395cd6f9ef1aa83343ec79d9c4404`. The compared topic authority artifact is lifecycle scope v2 (`1100c8...1753`); the compared structural-role artifact is v4 (`c35c...0274bc`).

## 8. Topic identity readback

The official `/api/v2/topic-catalog?limit=500&offset=0` returned 132 current entries as of 2026-09-15: 107 `LEAF` and 25 `PARENT`, with 132 unique IDs. The canonical identity set is an `EXACT_MATCH`: missing 0, extra 0, duplicate 0.

Normalized identity SHA-256 for canonical and Production is identical:

```text
06CB9DB776682B65BB68B9F97DA6272557B65E772E5F2400DEDF779026B2BC13
```

The direct DB MD5 cross-check is also identical: `34b5f2e4ab6ff3164c69e55d7f064bd3`.

## 9. Parent/child hierarchy

Direct DB readback produced 107 date-effective valid edges, 25 distinct parents, and 107 distinct leaves. There were 0 duplicate edges, 0 invalid parent/child edges, and 0 orphan active topic IDs. The normalized hierarchy is an `EXACT_MATCH`.

```text
CANONICAL_HIERARCHY_SHA256 = 40EEAFFA1BDA80873EEEFDA9BF0654222CCCA041A0B0C85AFC00C4EADE34BD34
PRODUCTION_HIERARCHY_SHA256 = 40EEAFFA1BDA80873EEEFDA9BF0654222CCCA041A0B0C85AFC00C4EADE34BD34
CANONICAL_HIERARCHY_MD5 = 155bd6e3535b663ae9ddab3a62eb5eee
PRODUCTION_HIERARCHY_MD5 = 155bd6e3535b663ae9ddab3a62eb5eee
```

## 10. Structural Role count and identity

The canonical artifact hash selected exactly 1,160 Production rows. All 1,160 relation IDs and all 1,160 authority tuples are unique. All rows have non-null structural role, `APPROVED` state, the exact authority version, exact source artifact ID/hash, exact approval reference, current topic linkage, and active instrument linkage.

## 11. Structural Role content

Role distribution matches the canonical artifact exactly:

```text
PRIMARY = 474
SECONDARY = 686
CORE = 650
REPRESENTATIVE = 329
RELATED = 181
```

The normalized authority content tuple `market|instrument|topic|relation_type|structural_role|approval_state` has identical MD5:

```text
CANONICAL_ROLE_MD5 = 6d2e7f0284060a439b6cb15163244630
PRODUCTION_ROLE_MD5 = 6d2e7f0284060a439b6cb15163244630
```

## 12. Version reconciliation

The full normalized key including `relation_version` differs only because Production preserves 440 existing `v1` membership versions while 720 rows use `owner-topic-membership-20260824.v1`. This exactly matches the role artifact reconciliation metadata (`expectedExistingProductionCount=440`, `expectedMissingProductionCount=720`). The structural authority version and source artifact linkage are exact for all 1,160 rows.

```text
CANONICAL_FULL_ROLE_KEY_MD5 = 5fbdba7ea2c3ad4632007d68bfa0985a
PRODUCTION_FULL_ROLE_KEY_MD5 = f27d5e3b8d41fc5346ea4641902d5224
```

Therefore the structural-role authority classification is `EXACT_PROVENANCE_MATCH`; the full-key difference is an expected membership-version reconciliation, not an authority-data mismatch.

## 13. Authority activation

`topicpilot.topic_authority_activations` contains an `ACTIVE` v2 row for Production / `neondb` with active counts 25 Parents, 107 Leaves, and lifecycle scope 107. Its topic artifact hash and source master hash exactly match the governed scope artifact.

## 14. Formal read model

The API catalog is available for all 132 topics as of 2026-09-15 and identifies the DB authorities as `topicpilot.topics`, `topicpilot.topic_hierarchy`, and `topicpilot.instrument_topic_relations`. Formal snapshot readback returns 92 complete formal/published rows dated 2026-09-09 across 92 distinct topics.

## 15. Publication boundary

This task did not publish or activate anything. The 92 snapshot rows carry `FORMAL/PUBLISHED`, but lifecycle quality remains `SHADOW_ONLY_UNPUBLISHED`; this is a separate publication/lifecycle gate and must not be conflated with the now-satisfied DB authority prerequisite.

## 16. Leader Set

Structural Role authority is present and approved, but the formal leadership/Leader Set policy is not activated in this task. Classification: `PRESENT_NOT_FORMAL`.

## 17. Current A10/A9 state

The Production DB is at canonical migration 0040. A9 formal writer DB prerequisite is `SATISFIED` by the exact authority readback. No A9 writer or activation was modified.

## 18. Parallel Layer2 policy task

`TASK-TOPIC-B2-LAYER2-FORMAL-POLICY-APPROVAL-001` remains separate and untouched. This readback does not approve Layer 2 policy.

## 19. Today boundary

Today code, schema, lifecycle, manifest, and reports were not modified.

## 20. Opportunity / Stock consequence

No Opportunity or Stock workstream was modified. Their DB readiness is reported as `PARTIAL` because this task proves the Topic authority DB only; their full downstream contracts were not independently gated here.

## 21. Evidence and reproducibility

Sanitized evidence files are:

- `production-readback-evidence.json`
- `readback-queries.sql`
- `continuation-evidence-manifest.txt`

The prior blocked-run manifest was integrity-checked before continuation. No passwords, tokens, cookies, connection strings, or private environment variables are included.

## 22. Final gate fields

```yaml
TASK: TASK-TOPIC-B2-107-25-FORMAL-DB-READBACK-001
MODE: ONE_SHOT_OPERATOR_READBACK_CONTINUATION
RESULT: COMPLETE
STOP_REASON: NONE
STATIC_BASELINE:
  LEAVES: 107
  PARENTS: 25
  STRUCTURAL_ROLE_ROWS: 1160
003F_GOVERNED_PROVENANCE: VERIFIED
PRODUCTION_DB_ACCESS: VERIFIED
READBACK_TIMESTAMP: 2026-09-15T12:33:14.768+08:00
PRODUCTION_DB_REVISION: 0040_task_a10_recovery_checkpoint_observability
LEAF_TOPIC_COUNT: 107
LEAF_TOPIC_COUNT_MATCH: YES
LEAF_TOPIC_IDENTITY: EXACT_MATCH
PARENT_TOPIC_COUNT: 25
PARENT_TOPIC_COUNT_MATCH: YES
PARENT_TOPIC_IDENTITY: EXACT_MATCH
TOPIC_HIERARCHY: EXACT_MATCH
STRUCTURAL_ROLE_COUNT: 1160
STRUCTURAL_ROLE_COUNT_MATCH: YES
STRUCTURAL_ROLE_CONTENT: EXACT_MATCH
STRUCTURAL_ROLE_AUTHORITY: EXACT_PROVENANCE_MATCH
CANONICAL_DATASET_HASH: 06CB9DB776682B65BB68B9F97DA6272557B65E772E5F2400DEDF779026B2BC13
PRODUCTION_DATASET_HASH: 06CB9DB776682B65BB68B9F97DA6272557B65E772E5F2400DEDF779026B2BC13
CANONICAL_HIERARCHY_HASH: 40EEAFFA1BDA80873EEEFDA9BF0654222CCCA041A0B0C85AFC00C4EADE34BD34
PRODUCTION_HIERARCHY_HASH: 40EEAFFA1BDA80873EEEFDA9BF0654222CCCA041A0B0C85AFC00C4EADE34BD34
CANONICAL_ROLE_HASH: 6d2e7f0284060a439b6cb15163244630
PRODUCTION_ROLE_HASH: 6d2e7f0284060a439b6cb15163244630
FORMAL_DB_CONTENT: VERIFIED
FORMAL_DB_PROVENANCE: VERIFIED
B2_FORMAL_DB_PREREQUISITE: SATISFIED
A9_FORMAL_WRITER_DB_PREREQUISITE: SATISFIED
OPPORTUNITY_DOWNSTREAM_DB_PREREQUISITE: PARTIAL
STOCK_DOWNSTREAM_DB_PREREQUISITE: PARTIAL
PRODUCTION_MUTATION: NONE
MIGRATION: NOT_PERFORMED
PUBLICATION: NOT_PERFORMED
C_DRIVE: UNTOUCHED
PUSH: NO
EVIDENCE_MANIFEST_SHA256: SEE continuation-evidence-manifest.txt
GOVERNANCE_SHA: NOT_REGISTERED_SEPARATE_EVIDENCE_HANDOFF
REPORT: E:/topicpilot-worktrees/TASK-TOPIC-B2-107-25-FORMAL-DB-READBACK-001-20260915/TASK-TOPIC-B2-107-25-FORMAL-DB-READBACK-001-CONTINUATION-20260915.md
PROJECT_MEMORY_RECOVERY_TEST: PASS
OWNER_DECISION_REQUIRED: NO
NEXT_GOVERNED_ACTION: SEPARATE_FORMAL_PUBLICATION_AND_LIFECYCLE_GATE_REVIEW
```

## 23. Clean closeout

```text
B2 FORMAL DB 107/25/1160 READBACK: VERIFIED
FORMAL DB CONTENT: VERIFIED
B2 DB PREREQUISITE: SATISFIED
FORMAL PUBLICATION: STILL SEPARATELY GOVERNED
```
