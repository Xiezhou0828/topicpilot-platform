# Fresh database validation

FRESH_DB_FULL_UPGRADE_STATUS=NOT_RUN_NO_TEST_DATABASE

No disposable PostgreSQL test database was available or authorized in this environment:
- Docker Desktop's Linux engine was not running.
- No PostgreSQL service was present.
- localhost:5432 was not accepting connections.
- No TEST_DATABASE_URL was configured.

No database was created, mutated, migrated, stamped, or downgraded. As a non-database substitute, offline SQL generation for alembic upgrade head --sql completed successfully with exit code 0, emitted 2,364 lines, and contained no missing-revision error.
