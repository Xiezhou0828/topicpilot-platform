# Alembic graph validation

Runtime: Python 3.12.10, Alembic 1.19.1.

Commands run in services/api:
- python -m alembic history --verbose
- python -m alembic heads --verbose
- python -m alembic branches --verbose
- static ScriptDirectory traversal from 0045

Results:
- CANDIDATE_ALEMBIC_HISTORY_STATUS=PASS
- CANDIDATE_ALEMBIC_HEAD_COUNT=1
- CANDIDATE_ALEMBIC_HEADS=0045_task_m1_formal_score_grade_publication
- PRODUCTION_REVISION_RECOGNIZED_BY_CANDIDATE=YES
- MISSING_REVISION_REFERENCE_COUNT=0
- ALL_REVISION_COUNT=46
- 0045 down revision is 0044_task_m1_formal_opportunity_publication.
- The existing 0029 branchpoint is an intentional historical branchpoint; it does not create a candidate head.
- Traversal from 0045 reaches the 0039 common ancestor.

The candidate has the exact single-head graph required by Recovery-005.
