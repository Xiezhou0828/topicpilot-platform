# Private parity evidence template

> Store completed records privately. Publish only sanitized aggregate evidence.

## Run identity

| Field | Value |
|---|---|
| Trading date (Asia/Taipei) | `YYYY-MM-DD` |
| Bundle version | |
| Bundle SHA-256 | |
| Source snapshot version/hash | |
| Application revision | |
| Migration head | |
| Parity query revision | |
| Target environment alias | |
| Operator/reviewer | |

## Import evidence

| Check | Expected | Actual | PASS/FAIL | Evidence reference |
|---|---:|---:|---|---|
| Contract validation | PASS | | | |
| Artifact hash validation | PASS | | | |
| Transactional import | completed | | | |
| Exact replay | no-op | | | |
| Error quality events | 0 | | | |

## Domain comparison

| Domain | Source rows/keys | PostgreSQL rows/keys | Null mismatch | Value mismatch | Result |
|---|---:|---:|---:|---:|---|
| Stocks | | | | | |
| Topics | | | | | |
| Topic hierarchy | | | | | |
| Stock-topic relations | | | | | |
| Market snapshots | | | | | |
| Stock snapshots | | | | | |
| Topic snapshots | | | | | |
| Strategy runs | | | | | |
| Strategy candidates | | | | | |
| Strategy performance | | | | | |

## Compatibility and quality

- Existing Snapshot validator result:
- API `data-status` version/date:
- Data-quality warning summary:
- Expected normalization applied:
- Sanitized discrepancy artifact:

## Discrepancies

| ID | Classification | Description | Blocking? | Owner | Corrective revision | Status |
|---|---|---|---:|---|---|---|
| | | | | | | |

## Sign-off

- Daily result: `PASS` / `FAIL`
- Consecutive PASS count:
- Operator date/sign-off:
- Reviewer date/sign-off:

## Ten-day summary

| Day | Trading date | Bundle version | Result | Notes |
|---:|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |

Final recommendation: `continue parallel` / `extend validation` /
`request separate PM source-of-truth decision`.
