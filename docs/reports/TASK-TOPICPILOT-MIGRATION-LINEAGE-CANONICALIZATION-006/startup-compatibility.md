# API startup compatibility simulation

The base and candidate were tested without a database by using Alembic's offline resolver.

- On d272, alembic upgrade 0045_task_m1_formal_score_grade_publication:head --sql fails with Can't locate revision identified by 0045_task_m1_formal_score_grade_publication.
- On the candidate, alembic upgrade head --sql completes with exit code 0, emits the full offline SQL plan, and contains no missing-revision error.
- The candidate's static revision resolver recognizes 0045 and the 0045-to-head traversal is empty.

Results:
- MISSING_0045_STARTUP_ERROR_REPRODUCES_ON_BASE=YES
- MISSING_0045_STARTUP_ERROR_REPRODUCES_ON_CANDIDATE=NO
- CANDIDATE_API_STARTUP_COMPATIBILITY_STATUS=PASS_OFFLINE_MIGRATION_RESOLUTION

This simulates the relevant migration preflight only. It does not start the Production API and does not deploy.
