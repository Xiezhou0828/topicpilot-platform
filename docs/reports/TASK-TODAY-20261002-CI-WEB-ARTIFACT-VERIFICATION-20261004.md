# Canonical Web artifact verification for the existing 10/2 closure

TASK_ID=TASK-TODAY-20261002-FINAL-PRODUCTION-PUBLICATION
TASK_TYPE=implementation/release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED

## Bounded verification repair

The Owner requests completion of the existing formal 10/2 publication and has
authorized necessary bounded successor fixes, CI, Owner-exception integration
and exact canonical release. Continue the same branch/worktree and mainline.
No independent reviewer, branch-protection change or failing-check waiver is
claimed. The local preview launch was denied before process creation. This
phase does not retry it through another local launcher or relax any guard.

The explicit, manual, read-only GitHub Actions verification workflow builds a
fresh locked canonical main artifact and executes its existing Cloudflare
Worker bundle in the runner's isolated local runtime. It never invokes a
deploy hook, Production database, migration, scheduler, comparator, provider
writer, recovery or POST_CLOSE. HTTPS verification uses a locally trusted
certificate with localhost SAN; TLS verification is not disabled.

## Evidence and trust boundary

- Retain canonical origin/main/HEAD/clean-source validation and the sorted
  path/length/SHA-256 manifest covering server and client bytes.
- Retain canonical source, Sites parent, digest, build timestamp and runtime
  source evidence. Build sidecars cannot attest a Production runtime.
- Read actual HTTPS runtime sidecar, HTML and same-origin loaded JS modules.
  Compare each served module to its canonical artifact bytes.
- Save the exact artifact and runtime receipt together, including hidden
  provenance sidecars. CI verification is explicitly NOT Production readback.
- At prepublish, require the live canonical main workflow_dispatch run to
  have succeeded, with exact source/workflow/ref/repository and first attempt.
  Require the exact named, unexpired GitHub artifact and verify the downloaded
  archive's SHA-256 against GitHub's digest. Compare every archived server,
  client and sidecar byte with the prospective Sites bundle. A local receipt,
  generic green CI, PR run, fork, re-run, missing digest or mismatched archive
  does not authorize publication.
- Retain supported Sites source push evidence, additive direct successor,
  exact committed artifact and all previous Sites-only history. No overwrite.
- After authorized native deployment, separately verify public Web runtime
  source and served asset bytes. API/Worker exact canonical revision and
  migration 0048 remain prerequisites for Home-only completion.

## Product and data boundaries

No application/provider/Topic/Score/Grade/Lifecycle/Opportunity/schema/API
contract change. No price/comparator reapply or second normal command.
The previously canonical Home-only completion contract remains the sole
unconsumed, separately authorized completion path; it still fails closed.
Run 2284, old 10/1 failed run and old 10/2 partial run remain untouched.
No history, synthetic price, zero-fill, forward-fill or manual SQL.

The bounded write set is the provenance guard, its synthetic regression tests,
the manual CI verification workflow, the existing CI regression-test hook,
and this report. Final exact commits, CI/artifact digest, deployment and
Production publication results belong in dated operational readback evidence.
Code or CI completion alone is not the required terminal state.

## Pre-commit validation and attribution

The 39 new synthetic provenance/receipt regressions pass. Full backend passed
1302 with 77 PostgreSQL-dependent skips, unchanged from the validated 259a6a3
application baseline; focused Home/request-shape tests passed 98. Frontend
passed 203, build/typecheck passed, and the generated client passed 4 with no
generated diff. Secret policy passed 18 cases with all four exact historical
exceptions verified; staged Gitleaks reported zero findings. OpenAPI is valid
and unchanged; migration graph remains 49 revisions, one 0048 head. The existing
frontend hook lint warning remains baseline debt, not fixed in this scope.
Changed Python/Ruff scope is empty; the earlier full-repo Ruff debt and isolated
PostgreSQL baseline failures are not waived or claimed repaired. A harmless
trailing-blank-line diff finding was removed before final commit validation.
