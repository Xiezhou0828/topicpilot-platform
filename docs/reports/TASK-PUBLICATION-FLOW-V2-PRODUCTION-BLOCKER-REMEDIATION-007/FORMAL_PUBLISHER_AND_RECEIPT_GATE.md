# Formal publisher and receipt gate

## Reused authority evidence

Task 006's authority inventory remains applicable: V1 is retired/disabled in the governed flow, the V2 result contract distinguishes non-success outcomes, and durable receipt/checkpoint semantics are defined. PR #79 passed the required CI and established the non-success CLI exit behavior.

Task 007 found no evidence of a second active formal writer. However, the actual Worker runtime is on 9703c956... and its post-close execution is currently fail-closed because of REFERENCE_PREFLIGHT_PendingRollbackError. The live writer's complete authority and permission path was not independently inspectable from the compact log stream.

SINGLE_FORMAL_PUBLISHER=PARTIAL
PUBLICATION_RESULT_SEMANTICS=PASS
DURABLE_RECEIPT_READINESS=PASS

No receipt was created, no publication writer was activated, and 2026-10-08 was not replayed. A later activation gate still needs a successful read-only preflight and confirmation that only the intended Worker can write formal receipts.
