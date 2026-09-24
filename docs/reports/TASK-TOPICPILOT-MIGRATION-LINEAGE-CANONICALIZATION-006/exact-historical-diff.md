# Exact historical migration restoration

- Base: d272fbef042ee520a2128a152751281dc89d4909
- Scope: exactly six historical Alembic modules, 0040 through 0045.
- Recovery evidence: E:/topicpilot-worktrees/TASK-TOPIC-FRONTEND-CANONICAL-HIERARCHY-RELEASE-READBACK-003/docs/reports/TASK-TOPICPILOT-PRODUCTION-MIGRATION-LINEAGE-RECOVERY-005/
- GitHub source: Xiezhou0828/topicpilot-platform

Each candidate Git blob SHA equals the SHA returned by the GitHub file read at the proven historical source commit. The equality covers the complete file bytes, including revision metadata, upgrade(), downgrade(), branch_labels, and depends_on; no formatting, renumbering, or cleanup was performed.

| Revision | Source commit | Source branch | Source blob | Candidate blob | Exact |
| --- | --- | --- | --- | --- | --- |
| 0040 | 51dbe48db203adb56e5fbc47da2f44b0e33997d2 | codex/a10-a9-isolated-quote-closure-20260912 | 20b5947c4e8441468e78f4adc46de59c892b2c5d | 20b5947c4e8441468e78f4adc46de59c892b2c5d | YES |
| 0041 | 6d9b87a22be955ab3c19871d17a39037acd968d7 | codex/task-m1-formal-pipeline-final-closure-001 | 0d0508e1fbdb5ae3c3dc48c3e180f6bee44c54aa | 0d0508e1fbdb5ae3c3dc48c3e180f6bee44c54aa | YES |
| 0042 | 6d9b87a22be955ab3c19871d17a39037acd968d7 | codex/task-m1-formal-pipeline-final-closure-001 | 32cb26c74be8a538c0f102ce5efe16264980fbd0 | 32cb26c74be8a538c0f102ce5efe16264980fbd0 | YES |
| 0043 | b1294010d8e51a2130a98a14cb39947e76ce8036 | codex/task-m1-formal-pipeline-final-closure-001 | 5f039ccb18dad71338d7be5cb3ec71b08a26bc2c | 5f039ccb18dad71338d7be5cb3ec71b08a26bc2c | YES |
| 0044 | 11ae11fcb7785d7dce52a6a4ffc619700cdf149f | codex/task-m1-formal-pipeline-final-closure-001 | 9bc0f54e44de0d4535527fa3678ce1026ec86a16 | 9bc0f54e44de0d4535527fa3678ce1026ec86a16 | YES |
| 0045 | 9fd442f4e5cc79ac65b23081fb53deb0233d553d | codex/task-m1-formal-pipeline-final-closure-001 | 425a1d39a420a99fe413a8057d66eda8be341c86 | 425a1d39a420a99fe413a8057d66eda8be341c86 | YES |

EXACT_HISTORICAL_FILE_MATCH_STATUS=PASS
REVISION_METADATA_EXACT_MATCH=PASS
UPGRADE_BODY_EXACT_MATCH=PASS
DOWNGRADE_BODY_EXACT_MATCH=PASS

No application, API, frontend, Today, Topic, or unrelated M1 files were imported.
