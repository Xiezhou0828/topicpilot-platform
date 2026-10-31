# Company Research V4 public read path

## Route and publication boundary

`GET /api/v2/stocks/{symbol}/research-v4` is a read-only projection for the
stock detail page and panel. It is separate from stock-master and Topic authority: a
research package cannot create an instrument, relation, role, or weight.

The API returns research content only when there is exactly one matching
`research_package.json` and its package and frontend contract versions are V4.
Publication can be authorized by a valid Owner approval, or by the standing
`RESEARCH_COMPLETENESS_GT_0_70_V1` policy when the finite numeric
`dataCompletenessScore` is strictly greater than 0.70, source rights are
approved, the company identity and V4 contract are valid, `blockingIssues` is
an explicit empty list, and the source register contains traceable HTTPS
references. Policy authorization records its
version, threshold, score, timestamp, and canonical content SHA-256 while
leaving `ownerReviewStatus=PENDING`; it is not represented as human review.
Scores at or below 0.70, explicit blocked/rejected states, non-empty or missing
`blockingIssues`, missing lineage,
invalid contracts, or unresolved source rights fail closed. The content hash
omits only authorization evidence fields, and the read path verifies the
attestation before returning data. Evidence registers, evidence IDs, approval
IDs, policy attestations, customer identities, and internal identifiers are
not projected.

The file adapter remains read-only and does not modify package files. A
successful package read is not evidence that stock-master, Topic relations,
the reference universe, or market-data collection is ready.

## Runtime configuration

Set `COMPANY_PROFILE_V4_READ_MODEL_PATH` to either one package file or a
read-only directory containing stock subdirectories with
`research_package.json` files. When the setting is absent or the path has no
matching package, the route returns `NOT_CONNECTED`; the UI does not substitute
Preview content for it.

The database-backed Production adapter reads only immutable public projections
written by the protected stock-add publisher; policy authorization does not
create a stock-master row or Topic relation. Production code and policy still
need to be deployed from the reviewed canonical commit before they take effect.

## Frontend behavior

The stock detail drawer requests the route only for formal stock reads. Preview
stocks do not make the request. Authorized overview, operating-matrix, theme,
and finance fields render in the Company Research section; other publication
states show a short generic message without exposing internal review metadata.
