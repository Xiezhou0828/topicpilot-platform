# Release / Deployment

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

**Summary role:** navigation only; repository, CI, deployment, and release
governance documents own the gates.

## Scope

This series covers V1/V2 generation boundaries, CI, release-candidate
qualification, deployment paths, exact-SHA provenance, rollback readiness, and
post-deploy verification.

## Current state

- V2 is the active platform path. V1 remains a protected legacy bridge until
  V2 replacement, dual-run/parity evidence, and an explicit cutover decision.
- CI and deployment paths are documented in `.github/workflows/`, the
  deployment architecture, and operations runbooks.
- Release-hygiene blockers are closed and WS4 records
  `READY_FOR_RELEASE_CHAIN_CLOSURE=YES`.
- The current boundary remains `READY_FOR_PRODUCTION_RELEASE=NO`: there is no
  committed release candidate, Production release, post-deploy verification,
  public revision claim, push, merge, or scheduler activation in this handoff.

## Canonical authority

- [`AGENTS.md` safety and promotion rules](../../AGENTS.md)
- [Deployment architecture](../architecture/10_DEPLOYMENT.md)
- [Deployment operations](../operations/deployment.md)
- [Operations runbook](../operations/runbook.md)
- [CI workflow](../../.github/workflows/ci.yml)
- [Deploy workflow](../../.github/workflows/deploy.yml)

## Completed

- V1/V2 generation and protected legacy-bridge boundary.
- CI and deployment topology documentation.
- Release-hygiene closure and current WS4 readiness classification.
- Exact-SHA, clean-source, reproducible-dependency, rollback, and deployed-
  revision requirements are defined.

## Unfinished / not released

- Owner-authorized release-chain closure and exact committed RC qualification.
- Clean checkout validation with reproducible dependencies.
- Production promotion, deployed revision verification, and post-deploy
  public/runtime checks.
- Any legacy bridge cutover or retirement.

## Dependencies and blockers

- Canonical commit and source-to-canonical provenance.
- Clean source state and reproducible dependency state.
- API/Web, migration/data, runtime revision, rollback, and owner-promotion
  evidence.

## Do not do

- Do not equate passing tests or `FINAL_STATUS=COMPLETE` with release.
- Do not deploy, push, merge, activate a scheduler, or change `NEXT_TASK`
  without the applicable Owner authorization.
- Do not use a dirty worktree or borrowed dependencies as final RC proof.
- Do not retire a protected V1 bridge because a V2 slice exists.

## Historical evidence

- [WS4 release-candidate qualification closure](../reports/TASK-OPS-WS4-RELEASE-CANDIDATE-QUALIFICATION-CANONICALIZATION-20260816.md)
- [SDLC canonical release governance](../reports/TASK-OPS-SDLC-CANONICAL-RELEASE-GOVERNANCE-RECONCILIATION-001.md)
- [Release-candidate canonical reconciliation](../reports/TASK-OPS-RELEASE-CANDIDATE-CANONICAL-RECONCILIATION-001.md)
- [Public-site release readiness](../reports/TASK-OPS-PUBLIC-SITE-RELEASE-READINESS-AND-CANONICAL-RECONCILIATION-001.md)
- [Release deployment path audit](../reports/TASK-OPS-PUBLIC-SITE-RELEASE-DEPLOYMENT-PATH-AUDIT-001.md)

## Next bounded route

Perform only the Owner-authorized release-chain closure for the exact
canonical commit. Keep capability completion, canonicalization, RC status,
Production release, and post-deploy verification as separate claims.
