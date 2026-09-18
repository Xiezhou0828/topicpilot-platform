---
name: topicpilot-incomplete-work-audit
description: Detect and classify unfinished, legacy, mock, placeholder, orphan, or unwired TopicPilot artifacts without deleting them.
---

Run scripts/governance/audit_incomplete_work.py against an explicit scope.
Search for TODO, FIXME, HACK, XXX, NotImplemented, placeholder, fixture,
synthetic, mock, legacy, deprecated, orphan, dead, and unwired indicators.

Report path, line, marker, and classification. Distinguish a detection from a
disposition: old, unused, unreferenced, or unwired does not prove ABANDONED.
Use PARTIAL, UNKNOWN, ORPHAN_CANDIDATE, or REVIEW_REQUIRED until an owner or
clear supersession evidence exists. Never delete, rename, or auto-rewrite
artifacts in this audit.
