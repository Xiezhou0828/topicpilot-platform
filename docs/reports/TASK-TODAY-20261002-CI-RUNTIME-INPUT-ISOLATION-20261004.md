# Bounded CI runtime-input isolation

Dated operational evidence: 2026-10-04. Same Owner-authorized 10/2 final
publication mainline, E-only checkout and existing branch. Required terminal
state remains POST_DEPLOY_VERIFIED; this report does not claim deployment.

Baseline canonical: d2673163bd861e5d50ab81c1fef85d5241dfd359.
PR64 CI37207955512 and canonical CI37208696933 passed all four checks.
Isolated artifact verification37208785823 failed before archive upload with
ARTIFACT_MANIFEST_MISMATCH. Build and Worker startup succeeded; no Production
deploy, Home completion, comparator apply or normal run was performed.

Installed Wrangler source creates .wrangler/tmp under the config project root
even for no-bundle execution. Runtime input therefore must not be the immutable
publishable directory. The bounded successor runs a byte-identical copy in
RUNNER_TEMP with separate persistent state, verifies every original manifest
file and sidecar before/after actual HTTPS execution, and packages ONLY the
unchanged original artifact. Tool scratch is never published. Strict artifact
manifest validation, CI archive digest and public runtime guards remain intact.

Regression proves scratch is permitted only for the disposable runtime copy;
the same extra file is rejected by the publication guard. Changes to server,
client or provenance input bytes still fail closed. No application, provider,
Topic, Score, Grade, Lifecycle, Opportunity, API, migration or Production policy
change. No denied local preview command was retried.

Validation and exact successor/canonical CI evidence are recorded in the owning
operational closure report; this commit remains implementation evidence until
canonical CI, exact artifact verification and three-end release/readback pass.
