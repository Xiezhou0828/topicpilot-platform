# Company Research V4 public read path

## Route and publication boundary

`GET /api/v2/stocks/{symbol}/research-v4` is a read-only projection for the
stock detail panel. It is separate from stock-master and Topic authority: a
research package cannot create an instrument, relation, role, or weight.

The API returns research content only when there is exactly one matching
`research_package.json`, its package and frontend contract versions are V4,
and its publication record says `PUBLISHED` with owner review, source rights,
and approval evidence all present. Approval evidence must include a SHA-256 of
the canonical package content with only `approvalEvidence` omitted; the read
path recomputes it before returning data. Editing a package after approval
therefore fails closed until it is reviewed and approved again. Missing,
duplicate, malformed, hash-mismatched, or unapproved packages return an empty
public envelope. Evidence registers,
evidence IDs, approval IDs, customer identities, and internal identifiers are
not projected.

The store is read-only. It performs no upload, edit, publication, migration, or
database write. A successful package read is not evidence that stock-master,
Topic relations, the reference universe, or market-data collection is ready.

## Runtime configuration

Set `COMPANY_PROFILE_V4_READ_MODEL_PATH` to either one package file or a
read-only directory containing stock subdirectories with
`research_package.json` files. When the setting is absent or the path has no
matching package, the route returns `NOT_CONNECTED`; the UI does not substitute
Preview content for it.

Production still requires an operator-controlled publication process that
places only Owner-approved packages at the configured read path and ensures
the API runtime cannot modify that source. No Production path, mount, package,
or environment variable was provisioned by this code change.

## Frontend behavior

The stock detail drawer requests the route only for formal stock reads. Preview
stocks do not make the request. Approved overview, operating-matrix, theme, and
finance fields render in the Company Research section; other publication
states show a short generic message without exposing internal review metadata.
