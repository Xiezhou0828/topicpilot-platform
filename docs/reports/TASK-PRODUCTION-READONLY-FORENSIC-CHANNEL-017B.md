# TASK-PRODUCTION-READONLY-FORENSIC-CHANNEL-017B

## Scope and disposition

This task implements the repository side of a governed Production
SELECT-only forensic readback channel. It does not execute the 2026-09-29
readback, retry the incident, repair its root cause, deploy any service, run a
migration, activate a scheduler, or mutate Production.

The source task evidence was re-read from the canonical repository history:

- 016 confirms migration 0047 and the governed Worker release/readback path;
- 017 keeps the incident classification at
  `UNKNOWN_INSUFFICIENT_EVIDENCE`; and
- 017A stopped before any Production query because no attested protected
  read-only channel existed.

The implementation is intentionally ready for Owner provisioning but cannot
claim Production role readiness. A GitHub API check at
`2026-09-30T01:14:53+08:00` and the final post-merge check reported that the
`production-readonly` Environment did not yet exist. No secret value was
requested or read.

## Exact provenance

```text
TASK_ID=TASK-PRODUCTION-READONLY-FORENSIC-CHANNEL-017B
TASK_TYPE=implementation
REQUIRED_TERMINAL_STATE=CANONICALIZED
INITIAL_MAIN_SHA=979f3509934b88a2dfbde507704b7511b42ac734
IMPLEMENTATION_SHA=4efe30f9b14ba87c9e7463d35e76a8fb92ca2ed1
FOLLOWUP_CI_COMMIT_SHA=cce88cdbaa4dcbcdc25873cd17a719e76164f726
FOLLOWUP_TEST_FIX_COMMIT_SHA=aeee7cd85c8cb75fcb683d762600d0c89b75af42
PR_24_MERGE_SHA=48780a567ea9fcfb18821f5168617bf5d11a18f4
PR_25_MERGE_SHA=cac367d5f396f9fc0c81b1adc64c56178befbc82
CANONICAL_MAIN_SHA=cac367d5f396f9fc0c81b1adc64c56178befbc82
MIGRATION_HEAD=0047_task_topic_role_strength_design_freeze
SEMANTICS_CHANGED=NO_PRODUCT_OR_WORKER_SEMANTICS; ADDITIVE_OPERATIONS_CHANNEL_ONLY
PRODUCTION_DEPENDENCY=YES; READBACK_ROLE_AND_ENVIRONMENT_NOT_PROVISIONED
WORKTREE_STATUS=ONLY_PREEXISTING_UNTRACKED_OWNER_REPORT_REMAINS
PR_24=https://github.com/Xiezhou0828/topicpilot-platform/pull/24
PR_25=https://github.com/Xiezhou0828/topicpilot-platform/pull/25
```

## Implemented controls

| Control | Implementation status |
|---|---|
| Fixed command allowlist | `POST_CLOSE_RUN_READBACK` only |
| Strict run-id validation | UUID v1-v5 canonical hyphenated form; bound parameter only |
| Exact tool SHA | Workflow rejects non-40-hex refs and checks checkout identity/ancestry |
| Protected Environment | Workflow requires `production-readonly` and required-reviewer preflight |
| Credential boundary | Only `TOPICPILOT_PRODUCTION_READONLY_DATABASE_URL`; no fallback to writer/migration URLs |
| Role identity | Verifies `current_user`, `session_user`, and expected protected role variable |
| Transaction boundary | `SET TRANSACTION READ ONLY`, `SHOW transaction_read_only`, and fail-closed assertion |
| Table scope | `live_collector_runs`, `live_collector_attempts`, `live_collector_checkpoints` only |
| Query surface | Repository-owned parameterized SELECT statements; no raw SQL input |
| Privilege probe | Reads SELECT/INSERT/UPDATE/DELETE/TRUNCATE capability flags without mutation probes |
| Artifact | Bounded, sanitized JSON with run, distributions, representatives, market split, and checkpoints |
| Public exposure | None; workflow connects directly through the protected Environment |

## Validation

```text
UNIT_TEST_STATUS=PASS; 15 passed
DISPOSABLE_POSTGRES_TEST_STATUS=PASS_IN_CI_RUN_36604719746
SECURITY_NEGATIVE_TEST_STATUS=PASS; invalid command/UUID/SHA, writable transaction, and SQL-surface tests
WORKFLOW_STATIC_TEST_STATUS=PASS
WORKFLOW_YAML_PARSE_STATUS=PASS
CHANGED_SCOPE_RUFF_STATUS=PASS
DIFF_CHECK_STATUS=PASS
CI_STATUS=PASS; RUN_36604719746
SANITIZED_ARTIFACT_STATUS=IMPLEMENTED_AND_SCHEMA_CHECKED; PRODUCTION_ARTIFACT_NOT_GENERATED
```

The disposable PostgreSQL test creates a temporary login in a local CI/test
database only, grants the three-table SELECT matrix, verifies the fixed
readback, and confirms the role cannot perform table mutations. It refuses
non-local database hosts and never targets Production.

## Provisioning blocker

The following owner/platform actions remain required before the first
Production acceptance readback:

1. Create the protected GitHub Environment `production-readonly` with at least
   one required reviewer and the appropriate deployment branch policy.
2. Provision a dedicated PostgreSQL login with only CONNECT, schema USAGE, and
   SELECT on the three approved tables; verify no inherited mutation role,
   object ownership, migration authority, or mutation-capable function access.
3. Store that login URL only as the Environment secret
   `TOPICPILOT_PRODUCTION_READONLY_DATABASE_URL`.
4. Store the exact expected login name as the Environment variable
   `TOPICPILOT_PRODUCTION_READONLY_ROLE`.

These actions must use the platform/database administrative path. They are not
performed by the application, the forensic CLI, or ordinary CI. Until they
are attested, the task remains:

```text
BLOCKED_OWNER_READONLY_ROLE_PROVISIONING_REQUIRED
```

## Required final status after canonical merge

```text
FORENSIC_WORKFLOW_CANONICAL=CANONICALIZED_ON_MAIN
FORENSIC_WORKFLOW=.github/workflows/production-forensic-readback.yml
FORENSIC_WORKFLOW_STATUS=IMPLEMENTED; PROTECTED_ENVIRONMENT_PREFLIGHT_REQUIRED
FORENSIC_COMMANDS_SUPPORTED=POST_CLOSE_RUN_READBACK
EXACT_SHA_REQUIRED=YES
ARBITRARY_SQL_ALLOWED=NO

PRODUCTION_READONLY_ENVIRONMENT=NOT_PROVISIONED
PRODUCTION_READONLY_ROLE=NOT_PROVISIONED
ROLE_PROVISIONING_STATUS=BLOCKED_OWNER_READONLY_ROLE_PROVISIONING_REQUIRED
TARGET_TABLE_SCOPE=topicpilot.live_collector_runs; topicpilot.live_collector_attempts; topicpilot.live_collector_checkpoints
READONLY_TRANSACTION_ENFORCED=IMPLEMENTED; NOT_PRODUCTION_ATTESTED
TRANSACTION_READONLY_READBACK=NOT_RUN
DATABASE_CURRENT_USER=NOT_VERIFIED
MUTATION_PRIVILEGES_PRESENT=UNVERIFIED

FIRST_ACCEPTANCE_RUN_ID=30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
FIRST_ACCEPTANCE_READBACK_STATUS=NOT_RUN_OWNER_PROVISIONING_REQUIRED
FIRST_ACCEPTANCE_RUN_STATUS=UNKNOWN_UNTIL_PROTECTED_READBACK
FIRST_ACCEPTANCE_FAILURE_347_STATUS=UNKNOWN_UNTIL_PROTECTED_READBACK
FIRST_ACCEPTANCE_SKIPPED_206_STATUS=UNKNOWN_UNTIL_PROTECTED_READBACK
FIRST_ACCEPTANCE_MARKET_SPLIT_STATUS=UNKNOWN_UNTIL_PROTECTED_READBACK
FIRST_ACCEPTANCE_CHECKPOINT_STATUS=UNKNOWN_UNTIL_PROTECTED_READBACK

PRODUCTION_DB_MUTATED=NO
POST_CLOSE_RETRIED=NO
DEPLOYMENT_PERFORMED=NO
SCHEDULER_CHANGED=NO
OBSERVATION_CHANGED=NO
TASK_017A_RESUMABLE=NO; ROLE/ENVIRONMENT FIRST
TASK_015_RESUMABLE=UNCHANGED

TASK_STATUS=BLOCKED_OWNER_READONLY_ROLE_PROVISIONING_REQUIRED
TASK_COMPLETE=NO
FOLLOW_UP_REQUIRED=YES
FOLLOW_UP_REASON=Owner must provision and attest the dedicated role and protected Environment, then run the first SELECT-only acceptance readback.
OWNER_DECISIONS_REQUIRED=Production role privilege matrix and protected Environment reviewer/provisioning approval
KNOWN_LIMITATIONS=No Production role, secret, Environment, current_user, transaction readback, or incident artifact was available in this execution.
CANONICAL_CI_RUN=36604719746; ALL_CHECKS_PASS
CANONICAL_MERGE_STATUS=PR_24_AND_PR_25_MERGED
ARTIFACTS=.github/workflows/production-forensic-readback.yml; services/api/src/topicpilot_api/production_forensic_readback.py; docs/operations/production-forensic-readback.md; services/api/tests/test_production_forensic_readback.py; services/api/tests/test_production_forensic_readback_postgres.py; services/api/tests/test_production_forensic_workflow.py
NEXT_RECOMMENDED_TASK=Provision production-readonly and execute the first SELECT-only acceptance readback for 30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
```

## Owner provisioning and acceptance addendum

Recorded for the explicitly authorized 017B continuation on 2026-09-30
(Asia/Taipei). The latest canonical `origin/main` was fetched before the
acceptance attempt and remained:

```text
CURRENT_MAIN_SHA=a565fa60668e562e07de06035ea95c5575f89b49
PRODUCTION_READONLY_ENVIRONMENT=READY
REQUIRED_REVIEWER_RULE=READY; Xiezhou0828
PRODUCTION_READONLY_ROLE=topicpilot_forensic_readonly
TOPICPILOT_PRODUCTION_READONLY_DATABASE_URL=CONFIGURED; VALUE_NOT_READ
ROLE_PROVISIONING_STATUS=OWNER_ATTESTED_PASS
```

The environment secret and variable were checked by metadata only. The
secret value was not read, printed, copied, or stored. The canonical workflow
was not modified. The Owner-provisioned Production role was not altered.

The one newly dispatched acceptance run was:

```text
FORENSIC_WORKFLOW_RUN_ID=36621398206
FORENSIC_TOOL_SHA=a565fa60668e562e07de06035ea95c5575f89b49
FIRST_ACCEPTANCE_RUN_ID=30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a
FORENSIC_COMMAND=POST_CLOSE_RUN_READBACK
```

Environment approval, exact-SHA checkout, input validation, CLI installation,
and the protected-environment preflight passed. The fixed readback command
then terminated with the sanitized workflow error `FORENSIC_QUERY_FAILED`.
The artifact validation and upload steps were skipped; no sanitized
Production artifact was produced. No retry, alternate SQL, public endpoint,
or administrative credential was used.

Because the artifact was not generated, the following remain unverified and
must not be inferred:

```text
DATABASE_CURRENT_USER=NOT_VERIFIED
TRANSACTION_READONLY_READBACK=NOT_VERIFIED
MUTATION_PRIVILEGES_PRESENT=UNVERIFIED
RUN_STATUS=UNVERIFIED
TPE/TWO_DISTRIBUTIONS=UNVERIFIED
FIRST_FAILED_CHECKPOINT=UNVERIFIED
FALLBACK_PATH_STATUS=UNVERIFIED
FALLBACK_AMPLIFICATION_STATUS=UNVERIFIED
INCIDENT_WORKER_RUNTIME_SHA=UNVERIFIED
INCIDENT_REFERENCE_VERSION=UNVERIFIED
```

The incident conclusion therefore remains:

```text
PRIMARY_ROOT_CAUSE=UNKNOWN_INSUFFICIENT_EVIDENCE
SECONDARY_CONTRIBUTING_CAUSES=UNRESOLVED
ROOT_CAUSE_CONFIDENCE=NONE
TASK_017A_STATUS=BLOCKED_FORENSIC_WORKFLOW_ACCEPTANCE
TASK_015_RESUMABLE=DO_NOT_CHANGE_AUTOMATICALLY
PRODUCTION_DB_MUTATED=NO
POST_CLOSE_RETRIED=NO
DEPLOYMENT_PERFORMED=NO
SCHEDULER_CHANGED=NO
OBSERVATION_CHANGED=NO
TASK_STATUS=BLOCKED_FORENSIC_WORKFLOW_ACCEPTANCE
TASK_COMPLETE=NO
NEXT_RECOMMENDED_TASK=Owner review of the sanitized FORENSIC_QUERY_FAILED channel failure; no rerun without a new explicit acceptance authorization
```
