"""Read complete stock and Topic authorities from the formal V2 API.

This module is intentionally GET-only. It rejects redirects, partial pages, and
unstable identity snapshots so a local stock-add plan cannot turn a stale or
partial response into an authoritative absence check.
"""

from __future__ import annotations

import hashlib
import json
import os
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
from zoneinfo import ZoneInfo

from .stock_add_workflow import (
    MASTER_MATCH_FOUND,
    MASTER_NO_MATCH,
    AuthorityReadEvidence,
)

FORMAL_API_BASE_URL = "https://topicpilot-api.onrender.com"
FORMAL_API_SOURCE = "TopicPilot V2 formal read API"
PROTECTED_DB_SOURCE = "TopicPilot protected Production catalog readback"
PROTECTED_DB_ROLE = "topicpilot_catalog_readonly"
PROTECTED_DB_ENVIRONMENT = "PRODUCTION_READ_ONLY"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 20
PAGE_SIZE_STOCKS = 1000
PAGE_SIZE_TOPICS = 500


class FormalAuthorityReadError(RuntimeError):
    """A formal read failed or could not prove a complete stable snapshot."""


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FormalAuthorityReadError("FORMAL_API_REDIRECT_REJECTED")


@dataclass(frozen=True)
class FormalAuthoritySnapshot:
    stock_items: tuple[dict, ...]
    topic_items: tuple[dict, ...]
    master_evidence: AuthorityReadEvidence
    topic_catalog_evidence: AuthorityReadEvidence
    read_controls: dict | None = None

    def stock_status(self, stock_code: str, market: str | None = None) -> str:
        requested = stock_code.strip().upper()
        requested_market = market.strip().upper() if market else None
        return (
            MASTER_MATCH_FOUND
            if any(
                str(item.get("code", item.get("symbol", ""))).strip().upper() == requested
                and (
                    requested_market is None
                    or str(item.get("market", "")).strip().upper() == requested_market
                )
                for item in self.stock_items
            )
            else MASTER_NO_MATCH
        )


def _fetch_formal_api(url: str) -> bytes:
    parsed = urlsplit(url)
    base = urlsplit(FORMAL_API_BASE_URL)
    if parsed.scheme != "https" or parsed.netloc != base.netloc:
        raise FormalAuthorityReadError("UNTRUSTED_FORMAL_API_ORIGIN")
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    opener = build_opener(
        _RejectRedirects(),
        HTTPSHandler(context=ssl.create_default_context()),
    )
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise FormalAuthorityReadError("FORMAL_API_NON_200_RESPONSE")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise FormalAuthorityReadError(f"FORMAL_API_HTTP_{exc.code}") from exc
    except URLError as exc:
        raise FormalAuthorityReadError("FORMAL_API_UNAVAILABLE") from exc
    if len(payload) > MAX_RESPONSE_BYTES:
        raise FormalAuthorityReadError("FORMAL_API_RESPONSE_TOO_LARGE")
    return payload


def _get_json(url: str, fetch: Callable[[str], bytes]) -> tuple[dict, bytes]:
    try:
        raw = fetch(url)
        payload = json.loads(raw.decode("utf-8"))
    except FormalAuthorityReadError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise FormalAuthorityReadError("FORMAL_API_INVALID_JSON") from exc
    if not isinstance(payload, dict):
        raise FormalAuthorityReadError("FORMAL_API_INVALID_PAGE_SHAPE")
    return payload, raw


def _require_non_synthetic_authority(fetch: Callable[[str], bytes]) -> None:
    """Refuse to treat a deployment that declares synthetic data as authority."""

    payload, _ = _get_json(f"{FORMAL_API_BASE_URL}/openapi.json", fetch)
    info = payload.get("info")
    description = info.get("description") if isinstance(info, dict) else None
    if not isinstance(description, str) or not description.strip():
        raise FormalAuthorityReadError("FORMAL_API_DATA_MODE_UNDECLARED")
    normalized = " ".join(description.casefold().split())
    if "synthetic data" in normalized:
        raise FormalAuthorityReadError("FORMAL_API_DECLARED_SYNTHETIC_DATA")


def _read_pages(
    *,
    endpoint: str,
    page_size: int,
    fetch: Callable[[str], bytes],
    pinned_as_of: str | None = None,
) -> tuple[tuple[dict, ...], tuple[bytes, ...], str | None]:
    items: list[dict] = []
    raw_pages: list[bytes] = []
    total: int | None = None
    as_of = pinned_as_of
    offset = 0
    pages = 0
    while True:
        params = {"limit": page_size, "offset": offset}
        if as_of is not None:
            params["asOf"] = as_of
        url = f"{FORMAL_API_BASE_URL}{endpoint}?{urlencode(params)}"
        page, raw = _get_json(url, fetch)
        pages += 1
        if pages > 100:
            raise FormalAuthorityReadError("FORMAL_API_PAGE_LIMIT_EXCEEDED")
        page_items = page.get("items")
        page_total = page.get("total")
        if (
            not isinstance(page_items, list)
            or not isinstance(page_total, int)
            or isinstance(page_total, bool)
            or page_total < 0
            or page.get("offset") != offset
            or page.get("limit") != page_size
        ):
            raise FormalAuthorityReadError("FORMAL_API_INVALID_PAGINATION_METADATA")
        if total is None:
            total = page_total
        elif total != page_total:
            raise FormalAuthorityReadError("FORMAL_API_TOTAL_CHANGED_DURING_READ")
        if endpoint == "/api/v2/topic-catalog":
            page_as_of = page.get("asOf")
            if not isinstance(page_as_of, str) or not page_as_of:
                raise FormalAuthorityReadError("FORMAL_TOPIC_CATALOG_MISSING_AS_OF")
            if as_of is None:
                as_of = page_as_of
            elif page_as_of != as_of:
                raise FormalAuthorityReadError("FORMAL_TOPIC_CATALOG_AS_OF_CHANGED")
        if any(not isinstance(item, dict) for item in page_items):
            raise FormalAuthorityReadError("FORMAL_API_INVALID_ITEM_SHAPE")
        if len(page_items) > page_size or (offset < page_total and not page_items):
            raise FormalAuthorityReadError("FORMAL_API_INCOMPLETE_PAGE")
        if offset + len(page_items) < page_total and len(page_items) != page_size:
            raise FormalAuthorityReadError("FORMAL_API_SHORT_NONFINAL_PAGE")
        items.extend(page_items)
        raw_pages.append(raw)
        offset += len(page_items)
        if offset >= page_total:
            break
    if total is None or len(items) != total:
        raise FormalAuthorityReadError("FORMAL_API_INCOMPLETE_UNIVERSE")
    return tuple(items), tuple(raw_pages), as_of


def _stock_identity_digest(items: tuple[dict, ...]) -> str:
    identities: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        code = str(item.get("code", item.get("symbol", ""))).strip().upper()
        market = str(item.get("market", "")).strip().upper()
        instrument_id = str(item.get("instrumentId", "")).strip()
        if (
            not code.isdigit()
            or len(code) not in {4, 6}
            or market not in {"TPE", "TWO"}
            or not instrument_id
            or not isinstance(item.get("name"), str)
            or not item["name"].strip()
        ):
            raise FormalAuthorityReadError("FORMAL_STOCK_IDENTITY_FIELDS_MISSING")
        key = (market, code)
        if key in seen:
            raise FormalAuthorityReadError("FORMAL_STOCK_IDENTITY_DUPLICATE")
        seen.add(key)
        identities.append(
            {
                "instrumentId": instrument_id,
                "code": code,
                "name": item.get("name"),
                "market": market,
                "exchange": item.get("exchange"),
                "listing": item.get("listing"),
                "active": item.get("active"),
                "enabled": item.get("enabled"),
                "instrumentType": item.get("instrumentType"),
                "currency": item.get("currency"),
                "validFrom": item.get("validFrom"),
                "validTo": item.get("validTo"),
            }
        )
    identities.sort(key=lambda item: (item["market"], item["code"]))
    return _canonical_digest(identities)


def _topic_identity_digest(items: tuple[dict, ...]) -> str:
    identities: list[dict] = []
    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    for item in items:
        topic_id = str(item.get("topicId", "")).strip()
        slug = str(item.get("slug", "")).strip()
        name = str(item.get("name", "")).strip()
        kind = item.get("kind")
        if not topic_id or not slug or not name or not isinstance(kind, str):
            raise FormalAuthorityReadError("FORMAL_TOPIC_IDENTITY_FIELDS_MISSING")
        if topic_id in seen_ids or slug in seen_slugs:
            raise FormalAuthorityReadError("FORMAL_TOPIC_IDENTITY_DUPLICATE")
        seen_ids.add(topic_id)
        seen_slugs.add(slug)
        identities.append(
            {
                "topicId": topic_id,
                "slug": slug,
                "name": name,
                "status": item.get("status"),
                "enabled": item.get("enabled"),
                "kind": kind,
                "hierarchy": item.get("hierarchy"),
                "validFrom": item.get("validFrom"),
                "validTo": item.get("validTo"),
                "dictionaryVersion": item.get("dictionaryVersion"),
            }
        )
    identities.sort(key=lambda item: (item["slug"], item["topicId"]))
    return _canonical_digest(identities)


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_evidence(
    *,
    digest: str,
    count: int,
    page_count: int,
    scope: str,
    as_of: str | None = None,
    source: str = FORMAL_API_SOURCE,
    environment: str = "PRODUCTION_READ_ONLY",
) -> AuthorityReadEvidence:
    return AuthorityReadEvidence(
        source=source,
        environment=environment,
        read_at=datetime.now(UTC).isoformat(timespec="seconds"),
        complete=True,
        sha256=digest,
        record_count=count,
        page_count=page_count,
        scope=scope,
        as_of=as_of,
    )


def read_formal_authority_snapshot(
    fetch: Callable[[str], bytes] = _fetch_formal_api,
) -> FormalAuthoritySnapshot:
    """Read and cross-check complete stock and Topic identity snapshots twice."""
    _require_non_synthetic_authority(fetch)
    stocks, stock_pages, _ = _read_pages(
        endpoint="/api/v2/stocks", page_size=PAGE_SIZE_STOCKS, fetch=fetch
    )
    stock_digest = _stock_identity_digest(stocks)
    stocks_repeat, _, _ = _read_pages(
        endpoint="/api/v2/stocks", page_size=PAGE_SIZE_STOCKS, fetch=fetch
    )
    if _stock_identity_digest(stocks_repeat) != stock_digest:
        raise FormalAuthorityReadError("FORMAL_STOCK_UNIVERSE_CHANGED_DURING_READ")

    topics, topic_pages, as_of = _read_pages(
        endpoint="/api/v2/topic-catalog", page_size=PAGE_SIZE_TOPICS, fetch=fetch
    )
    topic_digest = _topic_identity_digest(topics)
    topics_repeat, _, repeated_as_of = _read_pages(
        endpoint="/api/v2/topic-catalog",
        page_size=PAGE_SIZE_TOPICS,
        fetch=fetch,
        pinned_as_of=as_of,
    )
    if repeated_as_of != as_of or _topic_identity_digest(topics_repeat) != topic_digest:
        raise FormalAuthorityReadError("FORMAL_TOPIC_CATALOG_CHANGED_DURING_READ")

    return FormalAuthoritySnapshot(
        stock_items=stocks,
        topic_items=topics,
        master_evidence=_read_evidence(
            digest=stock_digest,
            count=len(stocks),
            page_count=len(stock_pages),
            scope="GET /api/v2/stocks; all markets; complete paginated identity universe",
        ),
        topic_catalog_evidence=_read_evidence(
            digest=topic_digest,
            count=len(topics),
            page_count=len(topic_pages),
            scope="GET /api/v2/topic-catalog; complete active Topic catalog",
            as_of=as_of,
        ),
    )


_CATALOG_TABLES = (
    "public.alembic_version",
    "topicpilot.markets",
    "topicpilot.instruments",
    "topicpilot.topics",
    "topicpilot.topic_hierarchy",
)


def _require_protected_workflow_context() -> tuple[str, str, str]:
    """Require the fixed repository's manually dispatched protected workflow."""

    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
        raise FormalAuthorityReadError("PROTECTED_DATABASE_READ_REQUIRES_GITHUB_ACTIONS")
    if os.environ.get("GITHUB_REPOSITORY") != "Xiezhou0828/topicpilot-platform":
        raise FormalAuthorityReadError("PROTECTED_DATABASE_READ_WRONG_REPOSITORY")
    if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise FormalAuthorityReadError("PROTECTED_DATABASE_READ_REQUIRES_MANUAL_DISPATCH")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise FormalAuthorityReadError("PROTECTED_DATABASE_READ_REQUIRES_CANONICAL_MAIN")
    expected_workflow_ref = (
        "Xiezhou0828/topicpilot-platform/.github/workflows/"
        "stock-add-authority-readback.yml@refs/heads/main"
    )
    if os.environ.get("GITHUB_WORKFLOW_REF", "").casefold() != expected_workflow_ref.casefold():
        raise FormalAuthorityReadError("PROTECTED_DATABASE_READ_WRONG_WORKFLOW")
    database_url = os.environ.get("TOPICPILOT_PRODUCTION_CATALOG_READONLY_DATABASE_URL")
    expected_role = os.environ.get("TOPICPILOT_PRODUCTION_CATALOG_READONLY_ROLE")
    expected_host = os.environ.get("TOPICPILOT_PRODUCTION_CATALOG_READONLY_EXPECTED_HOST")
    expected_database = os.environ.get("TOPICPILOT_PRODUCTION_CATALOG_READONLY_EXPECTED_DATABASE")
    if not database_url:
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READONLY_URL_NOT_CONFIGURED")
    if expected_role != PROTECTED_DB_ROLE:
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READONLY_ROLE_NOT_APPROVED")
    if not expected_host or not expected_database:
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READONLY_TARGET_NOT_CONFIGURED")
    from sqlalchemy.engine import make_url

    try:
        parsed_url = make_url(database_url)
    except Exception:
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READONLY_DATABASE_URL_INVALID") from None
    if not parsed_url.drivername.startswith("postgresql"):
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READONLY_DATABASE_TYPE_INVALID")
    if (
        not parsed_url.host
        or parsed_url.host.casefold() != expected_host.strip().casefold()
        or parsed_url.database != expected_database.strip()
    ):
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READONLY_TARGET_MISMATCH")
    return database_url, expected_role, expected_database.strip()


def _database_rows(connection, statement: str, parameters: dict | None = None) -> list[dict]:
    from sqlalchemy import text

    result = connection.execute(text(statement), parameters or {})
    return [dict(row) for row in result.mappings()]


def _verify_protected_read_connection(
    connection, expected_role: str, expected_database: str
) -> dict:
    """Fail closed unless this is the exact least-privilege read-only role."""

    from sqlalchemy import text

    connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
    transaction_read_only = str(
        connection.execute(text("SHOW transaction_read_only")).scalar_one()
    ).lower()
    isolation = str(connection.execute(text("SHOW transaction_isolation")).scalar_one()).lower()
    database_name = str(connection.execute(text("SELECT current_database()")).scalar_one())
    if database_name != expected_database:
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READONLY_TARGET_MISMATCH")
    identity = _database_rows(
        connection,
        """
        SELECT current_user AS current_user,
               session_user AS session_user,
               role_record.rolname,
               role_record.rolsuper,
               role_record.rolcreatedb,
               role_record.rolcreaterole,
               role_record.rolreplication,
               role_record.rolbypassrls,
               role_record.rolinherit,
               role_record.rolcanlogin,
               (SELECT count(*)
                  FROM pg_catalog.pg_auth_members membership
                 WHERE membership.member = role_record.oid) AS granted_role_count,
               (SELECT db_catalog.datdba = current_user_oid.oid
                  FROM pg_catalog.pg_database db_catalog
                  JOIN pg_catalog.pg_roles current_user_oid
                    ON current_user_oid.rolname = current_user
                 WHERE db_catalog.datname = current_database()) AS is_database_owner,
               has_database_privilege(current_user, current_database(), 'CREATE')
                   AS can_create_database_objects,
               has_database_privilege(current_user, current_database(), 'TEMPORARY')
                   AS effective_temporary_privilege,
               COALESCE((
                   SELECT bool_or(acl.privilege_type IN ('CREATE', 'TEMPORARY'))
                     FROM pg_catalog.pg_database db_catalog
                     CROSS JOIN LATERAL pg_catalog.aclexplode(
                         COALESCE(db_catalog.datacl,
                                  pg_catalog.acldefault('d', db_catalog.datdba))
                     ) acl
                    WHERE db_catalog.datname = current_database()
                      AND acl.grantee = role_record.oid
               ), FALSE) AS direct_database_mutation_privilege
          FROM pg_catalog.pg_roles role_record
         WHERE role_record.rolname = current_user
        """,
    )
    if len(identity) != 1:
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_DATABASE_ROLE_UNVERIFIED")
    row = identity[0]
    if (
        row.get("current_user") != expected_role
        or row.get("session_user") != expected_role
        or row.get("rolname") != expected_role
        or row.get("rolsuper") is not False
        or row.get("rolcreatedb") is not False
        or row.get("rolcreaterole") is not False
        or row.get("rolreplication") is not False
        or row.get("rolbypassrls") is not False
        or row.get("rolinherit") is not False
        or row.get("rolcanlogin") is not True
        or row.get("granted_role_count") != 0
        or row.get("is_database_owner") is not False
        or row.get("can_create_database_objects") is not False
        or row.get("direct_database_mutation_privilege") is not False
        or transaction_read_only not in {"on", "true", "1"}
        or isolation != "repeatable read"
    ):
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READ_ONLY_IDENTITY_CHECK_FAILED")

    privilege_rows = _database_rows(
        connection,
        """
        SELECT required.table_name,
               has_table_privilege(current_user, required.table_name, 'SELECT') AS can_select,
               has_table_privilege(current_user, required.table_name, 'INSERT') AS can_insert,
               has_table_privilege(current_user, required.table_name, 'UPDATE') AS can_update,
               has_table_privilege(current_user, required.table_name, 'DELETE') AS can_delete,
               has_table_privilege(current_user, required.table_name, 'TRUNCATE') AS can_truncate,
               has_table_privilege(current_user, required.table_name,
                                   'REFERENCES') AS can_reference,
               has_any_column_privilege(current_user, required.table_name,
                                        'INSERT') AS can_insert_column,
               has_any_column_privilege(current_user, required.table_name,
                                        'UPDATE') AS can_update_column,
               has_any_column_privilege(current_user, required.table_name,
                                         'REFERENCES') AS can_reference_column,
               has_table_privilege(current_user, required.table_name, 'TRIGGER') AS can_trigger
          FROM (VALUES
                ('public.alembic_version'),
                ('topicpilot.markets'),
                ('topicpilot.instruments'),
                ('topicpilot.topics'),
                ('topicpilot.topic_hierarchy')
          ) AS required(table_name)
        """,
    )
    if len(privilege_rows) != len(_CATALOG_TABLES):
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_PRIVILEGE_SCOPE_UNVERIFIED")
    for privilege in privilege_rows:
        if privilege.get("can_select") is not True or any(
            privilege.get(key) is not False
            for key in (
                "can_insert",
                "can_update",
                "can_delete",
                "can_truncate",
                "can_reference",
                "can_insert_column",
                "can_update_column",
                "can_reference_column",
                "can_trigger",
            )
        ):
            raise FormalAuthorityReadError("PRODUCTION_CATALOG_ROLE_HAS_UNSAFE_TABLE_PRIVILEGES")
    unexpected_relation_privileges = _database_rows(
        connection,
        """
        SELECT count(*) AS privilege_count
          FROM pg_catalog.pg_class relation
          JOIN pg_catalog.pg_namespace namespace ON namespace.oid = relation.relnamespace
         WHERE namespace.nspname IN ('public', 'topicpilot')
           AND relation.relkind IN ('r', 'p', 'v', 'm', 'f')
           AND NOT (
               (namespace.nspname = 'public' AND relation.relname = 'alembic_version')
               OR (namespace.nspname = 'topicpilot' AND relation.relname IN
                   ('markets', 'instruments', 'topics', 'topic_hierarchy'))
           )
           AND (
               has_table_privilege(current_user, relation.oid, 'SELECT')
               OR has_table_privilege(current_user, relation.oid, 'INSERT')
               OR has_table_privilege(current_user, relation.oid, 'UPDATE')
               OR has_table_privilege(current_user, relation.oid, 'DELETE')
               OR has_table_privilege(current_user, relation.oid, 'TRUNCATE')
               OR has_table_privilege(current_user, relation.oid, 'REFERENCES')
               OR has_table_privilege(current_user, relation.oid, 'TRIGGER')
           )
        """,
    )
    if (
        len(unexpected_relation_privileges) != 1
        or unexpected_relation_privileges[0].get("privilege_count") != 0
    ):
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_ROLE_HAS_UNEXPECTED_RELATION_PRIVILEGE")
    sequence_privileges = _database_rows(
        connection,
        """
        SELECT count(*) AS privilege_count
          FROM pg_catalog.pg_class sequence
          JOIN pg_catalog.pg_namespace namespace ON namespace.oid = sequence.relnamespace
         WHERE namespace.nspname IN ('public', 'topicpilot')
           AND sequence.relkind = 'S'
           AND (
               has_sequence_privilege(current_user, sequence.oid, 'USAGE')
               OR has_sequence_privilege(current_user, sequence.oid, 'SELECT')
               OR has_sequence_privilege(current_user, sequence.oid, 'UPDATE')
           )
        """,
    )
    if len(sequence_privileges) != 1 or sequence_privileges[0].get("privilege_count") != 0:
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_ROLE_HAS_SEQUENCE_PRIVILEGE")
    schema_privileges = _database_rows(
        connection,
        """
        SELECT has_schema_privilege(current_user, 'public', 'CREATE') AS public_create,
               has_schema_privilege(current_user, 'topicpilot', 'CREATE') AS topicpilot_create
        """,
    )
    if (
        len(schema_privileges) != 1
        or schema_privileges[0].get("public_create") is not False
        or schema_privileges[0].get("topicpilot_create") is not False
    ):
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_ROLE_HAS_SCHEMA_CREATE_PRIVILEGE")
    return {
        "databaseRole": expected_role,
        "databaseTargetVerified": True,
        "sessionUser": expected_role,
        "transactionReadOnly": True,
        "transactionIsolation": isolation,
        "allowedTables": list(_CATALOG_TABLES),
        "mutationPrivilegesObserved": False,
        "directDatabaseMutationPrivilegeObserved": False,
        "effectiveTemporaryPrivilegeObserved": (row.get("effective_temporary_privilege") is True),
    }


def read_protected_database_authority_snapshot(
    *, stock_code: str, market: str
) -> FormalAuthoritySnapshot:
    """Read the live Production stock and Topic catalogs inside a protected CI job.

    This path is deliberately unavailable to local callers and uses a dedicated
    role that can SELECT only the fixed catalog tables. It never writes.
    """

    code = stock_code.strip()
    market_code = market.strip().upper()
    if not code.isdigit() or len(code) not in {4, 6} or market_code not in {"TPE", "TWO"}:
        raise FormalAuthorityReadError("INVALID_STOCK_CATALOG_QUERY")
    database_url, expected_role, expected_database = _require_protected_workflow_context()
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url

    parsed_url = make_url(database_url)
    if parsed_url.drivername == "postgresql":
        parsed_url = parsed_url.set(drivername="postgresql+psycopg")
    engine = create_engine(parsed_url, pool_pre_ping=True)
    as_of = datetime.now(ZoneInfo("Asia/Taipei")).date()
    try:
        with engine.connect() as connection, connection.begin():
            controls = _verify_protected_read_connection(
                connection, expected_role, expected_database
            )
            version_rows = _database_rows(
                connection,
                "SELECT version_num FROM public.alembic_version ORDER BY version_num",
            )
            if len(version_rows) != 1 or not version_rows[0].get("version_num"):
                raise FormalAuthorityReadError("PRODUCTION_CATALOG_MIGRATION_HEAD_UNVERIFIED")
            controls["migrationHead"] = version_rows[0]["version_num"]
            active_markets = _database_rows(
                connection,
                """
                    SELECT code, name, exchange_code, timezone, calendar_code
                      FROM topicpilot.markets
                     WHERE is_active IS TRUE
                       AND code IN ('TPE', 'TWO')
                       AND (valid_from IS NULL OR valid_from <= :as_of)
                       AND (valid_to IS NULL OR valid_to >= :as_of)
                     ORDER BY code
                    """,
                {"as_of": as_of},
            )
            if [row.get("code") for row in active_markets] != ["TPE", "TWO"]:
                raise FormalAuthorityReadError("PRODUCTION_CATALOG_MARKET_SCOPE_INCOMPLETE")
            controls["activeMarketCodes"] = [row["code"] for row in active_markets]
            stock_rows = _database_rows(
                connection,
                """
                    SELECT i.id AS instrument_id,
                           i.instrument_code AS code,
                           i.name,
                           m.code AS market,
                           m.exchange_code AS exchange,
                           i.instrument_type,
                           i.currency,
                           i.valid_from,
                           i.valid_to,
                           i.is_active AS active,
                           (i.valid_from IS NULL OR i.valid_from <= :as_of)
                             AND (i.valid_to IS NULL OR i.valid_to >= :as_of) AS enabled
                      FROM topicpilot.instruments i
                      JOIN topicpilot.markets m ON m.id = i.market_id
                     WHERE m.code IN ('TPE', 'TWO')
                       AND i.instrument_type = 'EQUITY'
                     ORDER BY m.code, i.instrument_code, i.id
                    """,
                {"as_of": as_of},
            )
            stocks = tuple(
                {
                    "instrumentId": str(row["instrument_id"]),
                    "code": str(row["code"]),
                    "name": row.get("name"),
                    "market": row["market"],
                    "exchange": row.get("exchange"),
                    "listing": "上市" if row["market"] == "TPE" else "上櫃",
                    "instrumentType": row["instrument_type"],
                    "currency": row["currency"],
                    "validFrom": row["valid_from"].isoformat() if row.get("valid_from") else None,
                    "validTo": row["valid_to"].isoformat() if row.get("valid_to") else None,
                    "active": row["active"],
                    "enabled": row["enabled"],
                }
                for row in stock_rows
            )
            if not stocks:
                raise FormalAuthorityReadError("PRODUCTION_STOCK_MASTER_EMPTY")
            stock_digest = _stock_identity_digest(stocks)

            topic_rows = _database_rows(
                connection,
                """
                    SELECT id AS topic_id, slug, name, status,
                           valid_from, valid_to, dictionary_version
                      FROM topicpilot.topics
                     ORDER BY slug, id
                    """,
            )
            if not topic_rows:
                raise FormalAuthorityReadError("PRODUCTION_TOPIC_CATALOG_EMPTY")
            hierarchy_rows = _database_rows(
                connection,
                """
                    SELECT hierarchy.parent_topic_id,
                           parent.slug AS parent_slug,
                           parent.name AS parent_name,
                           hierarchy.child_topic_id,
                           child.slug AS child_slug,
                           child.name AS child_name
                      FROM topicpilot.topic_hierarchy hierarchy
                      JOIN topicpilot.topics parent ON parent.id = hierarchy.parent_topic_id
                      JOIN topicpilot.topics child ON child.id = hierarchy.child_topic_id
                     WHERE hierarchy.valid_from <= :as_of
                       AND (hierarchy.valid_to IS NULL OR hierarchy.valid_to >= :as_of)
                     ORDER BY parent.slug, child.slug, hierarchy.id
                    """,
                {"as_of": as_of},
            )
            topic_ids = {str(row["topic_id"]) for row in topic_rows}
            edges: dict[str, dict[str, list[dict]]] = {
                topic_id: {"parents": [], "children": []} for topic_id in topic_ids
            }
            seen_edges: set[tuple[str, str]] = set()
            for edge in hierarchy_rows:
                parent_id = str(edge["parent_topic_id"])
                child_id = str(edge["child_topic_id"])
                if parent_id not in topic_ids or child_id not in topic_ids or parent_id == child_id:
                    raise FormalAuthorityReadError("PRODUCTION_TOPIC_HIERARCHY_INVALID")
                if (parent_id, child_id) in seen_edges:
                    raise FormalAuthorityReadError("PRODUCTION_TOPIC_HIERARCHY_DUPLICATE")
                seen_edges.add((parent_id, child_id))
                edges[child_id]["parents"].append(
                    {"topicId": parent_id, "slug": edge["parent_slug"], "name": edge["parent_name"]}
                )
                edges[parent_id]["children"].append(
                    {"topicId": child_id, "slug": edge["child_slug"], "name": edge["child_name"]}
                )
            topics = tuple(
                {
                    "topicId": str(row["topic_id"]),
                    "slug": row["slug"],
                    "name": row["name"],
                    "status": row["status"],
                    "validFrom": row["valid_from"].isoformat() if row.get("valid_from") else None,
                    "validTo": row["valid_to"].isoformat() if row.get("valid_to") else None,
                    "dictionaryVersion": row.get("dictionary_version"),
                    "enabled": (
                        str(row["status"]).upper() in {"ACTIVE", "ENABLED", "PUBLISHED"}
                        and (row.get("valid_from") is None or row["valid_from"] <= as_of)
                        and (row.get("valid_to") is None or row["valid_to"] >= as_of)
                    ),
                    "kind": "PARENT" if edges[str(row["topic_id"])]["children"] else "LEAF",
                    "hierarchy": edges[str(row["topic_id"])],
                }
                for row in topic_rows
            )
            topic_digest = _topic_identity_digest(topics)
    except FormalAuthorityReadError:
        raise
    except Exception as exc:
        raise FormalAuthorityReadError("PRODUCTION_CATALOG_READ_FAILED") from exc
    finally:
        engine.dispose()

    read_at = datetime.now(UTC).isoformat(timespec="seconds")
    return FormalAuthoritySnapshot(
        stock_items=stocks,
        topic_items=topics,
        master_evidence=AuthorityReadEvidence(
            source=PROTECTED_DB_SOURCE,
            environment=PROTECTED_DB_ENVIRONMENT,
            read_at=read_at,
            complete=True,
            sha256=stock_digest,
            record_count=len(stocks),
            page_count=1,
            scope="Protected repeatable-read snapshot of all TPE/TWO EQUITY identities",
        ),
        topic_catalog_evidence=AuthorityReadEvidence(
            source=PROTECTED_DB_SOURCE,
            environment=PROTECTED_DB_ENVIRONMENT,
            read_at=read_at,
            complete=True,
            sha256=topic_digest,
            record_count=len(topics),
            page_count=1,
            scope="Protected repeatable-read snapshot of all Topics and effective hierarchy",
            as_of=as_of.isoformat(),
        ),
        read_controls={**controls, "migrationHead": version_rows[0]["version_num"]},
    )


__all__ = [
    "FORMAL_API_BASE_URL",
    "FORMAL_API_SOURCE",
    "PROTECTED_DB_SOURCE",
    "FormalAuthorityReadError",
    "FormalAuthoritySnapshot",
    "read_formal_authority_snapshot",
    "read_protected_database_authority_snapshot",
]
