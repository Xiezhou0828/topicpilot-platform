# TASK-WS4-REFERENCE-INSTRUMENT-LIFECYCLE-1563-SUSPENSION-20260831

## Scope

This change handles the single \`1563 / TPE / 巧新\` capital-reduction trading
suspension. It does not change collector completeness semantics, publication
policy, lifecycle V1/V1.2, or successor-identity inference.

## Accepted source facts

The MOPS official major-announcement authority records:

- old-share last trading date: \`2026-08-26\`;
- old-share market suspension: \`2026-08-27\` through \`2026-09-04\`;
- new-share listing and trading start: \`2026-09-07\`.

The authority portal is:
https://mops.twse.com.tw/mops/web/t05st01

The complete announcement text was cross-checked against the published
announcement mirror, which identifies the same issuer, dates, and 25% cash
capital reduction:
https://wealth.firstbank.com.tw/investment-tips/trend-insight/news/news-detail?id=%7B80A60DF8-64D0-4CAD-8696-5B065A2C825A%7D

## Canonical interpretation

\`1563 / TPE\` remains the same physical instrument identity. The exchange
period is represented by one effective-dated \`SUSPENDED\` lifecycle row:

\`\`\`text
effective_from = 2026-08-27
effective_to = 2026-09-04
\`\`\`

No \`TERMINATED\` row and no successor instrument were added.

## Validation

- reference bundle validator: PASS;
- reference bundle tests: 3 passed;
- no-trade contract tests: 10 passed;
- reference transition tests: 5 passed, 2 PostgreSQL integration tests skipped
  because no local PostgreSQL test database was configured;
- 2026-08-28 date-effective classification: \`SUSPENDED\`;
- no fake, zero, or synthetic price was introduced.

## Production boundary

The production code has now been deployed at the validated task commit. The
production reference registry has not been mutated by this task. The
production active reference remains:

\`\`\`text
reference version: tw-reference-v1-rollover-66edf7395785c4a1
bundle SHA-256: 66edf7395785c4a19f36c39d22911b83843621f5cfdda49f90ea42099fa9a543
\`\`\`

The reviewed candidate bundle is:

\`\`\`text
candidate bundle SHA-256: 55684037eef58f1068ea7ba6eaabd74f2e58f6967ea7b1db8ebe9255bcd9cca7
derived target version: tw-reference-v1-rollover-55684037eef58f10
\`\`\`

The candidate must first be deployed at the task commit and passed through
the dry-run transition command. Only then may an Owner separately authorize
the \`--activate\` command. This transition changes reference-only tables and
does not authorize Home materialization.

Deployed code commit:

\`\`\`text
efb7ebe2daf68d99d6a7d78f2ca46153ad49a255
\`\`\`

## Status

\`\`\`text
LOCAL_REFERENCE_FIX=PASS
1563_SUSPENDED_EFFECTIVE_DATE=2026-08-27
1563_SUSPENDED_END_DATE=2026-09-04
1563_RESUMPTION_DATE=2026-09-07
SUCCESSOR_INFERENCE=NO
PRODUCTION_MUTATION=NO
DEPLOY=YES
PUSH=NO
HOME_PUBLICATION=NOT_TOUCHED
\`\`\`
