"""Narrow, hash-bound Production writer for one new stock-master identity.

This module writes only ``markets``-referenced ``instruments``, immutable public
research publications, and the append-only stock-add operation journal. Topic
relations and reference-universe activation are separate governed stages.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from sqlalchemy import Connection, text

from .company_profile_v4.store import (
    prepare_research_publication,
    project_approved_package,
    publication_authorization_summary,
)
from .reference_data.bootstrap import canonical_instrument_id

PLAN_SCHEMA = "topicpilot-stock-add-master-plan.v1"
APPLY_CONFIRMATION_PREFIX = "APPLY STOCK ADD"
SUPPORTED_MARKETS = frozenset({"TPE", "TWO"})
EXPECTED_MIGRATION_HEAD = "0052_company_research_publications"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class StockAddWriterError(ValueError):
    """Raised when a stock-master add plan fails a safety precondition."""


@dataclass(frozen=True)
class StockAddMasterResult:
    status: str
    operation_id: str
    plan_sha256: str
    market: str
    stock_code: str
    instrument_id: str | None
    created: bool
    publication_version: int | None
    action: str
    publication_authorization: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "operationId": self.operation_id,
            "planSha256": self.plan_sha256,
            "market": self.market,
            "stockCode": self.stock_code,
            "instrumentId": self.instrument_id,
            "created": self.created,
            "publicationVersion": self.publication_version,
            "action": self.action,
            "publicationAuthorization": self.publication_authorization,
            "requiredConfirmation": expected_confirmation(
                self.market, self.stock_code, self.plan_sha256
            ),
            "writeSet": (["instruments"] if self.action == "ADD_INSTRUMENT_AND_PUBLISH" else [])
            + [
                "company_research_publications",
                "stock_add_operations",
                "stock_add_operation_events",
            ],
        }


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise StockAddWriterError(f"{name} must be a lowercase SHA-256")
    return value


def validate_master_plan(plan: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    """Validate a readback-bound approved package and return payload, digest and operation ID."""

    if not isinstance(plan, dict) or set(plan) != {
        "schemaVersion",
        "stock",
        "researchPackage",
        "masterReadback",
        "planSha256",
    }:
        raise StockAddWriterError("INVALID_PLAN_FIELDS")
    if plan.get("schemaVersion") != PLAN_SCHEMA:
        raise StockAddWriterError("UNSUPPORTED_PLAN_SCHEMA")
    stock = plan.get("stock")
    research_package = plan.get("researchPackage")
    readback = plan.get("masterReadback")
    if not isinstance(stock, dict) or set(stock) != {
        "market",
        "stockCode",
        "name",
        "instrumentType",
        "currency",
        "validFrom",
        "validFromEvidenceUrl",
    }:
        raise StockAddWriterError("INVALID_STOCK_FIELDS")
    if not isinstance(research_package, dict):
        raise StockAddWriterError("RESEARCH_PACKAGE_REQUIRED")
    if not isinstance(readback, dict) or set(readback) != {
        "status",
        "source",
        "environment",
        "readAt",
        "complete",
        "sha256",
    }:
        raise StockAddWriterError("INVALID_MASTER_READBACK_FIELDS")

    market = str(stock["market"]).strip().upper()
    code = str(stock["stockCode"]).strip()
    name = str(stock["name"]).strip()
    if market not in SUPPORTED_MARKETS or not re.fullmatch(r"\d{4,6}", code) or not name:
        raise StockAddWriterError("INVALID_STOCK_IDENTITY")
    if stock["instrumentType"] != "EQUITY" or stock["currency"] != "TWD":
        raise StockAddWriterError("UNSUPPORTED_STOCK_CLASSIFICATION")
    if stock["validFrom"] is not None:
        try:
            valid_from = date.fromisoformat(str(stock["validFrom"]))
        except (TypeError, ValueError) as exc:
            raise StockAddWriterError("OFFICIAL_VALID_FROM_INVALID") from exc
        stock["validFrom"] = valid_from.isoformat()
        source_url = stock["validFromEvidenceUrl"]
        if not isinstance(source_url, str) or not source_url.startswith("https://"):
            raise StockAddWriterError("OFFICIAL_VALID_FROM_SOURCE_REQUIRED")
        host = (urlsplit(source_url).hostname or "").lower()
        if not (
            host == "twse.com.tw"
            or host.endswith(".twse.com.tw")
            or host == "tpex.org.tw"
            or host.endswith(".tpex.org.tw")
            or host == "mops.twse.com.tw"
        ):
            raise StockAddWriterError("OFFICIAL_VALID_FROM_SOURCE_UNSUPPORTED")
    elif stock["validFromEvidenceUrl"] is not None:
        raise StockAddWriterError("VALID_FROM_SOURCE_WITHOUT_DATE")

    company = research_package.get("company")
    if not isinstance(company, dict):
        raise StockAddWriterError("RESEARCH_PACKAGE_IDENTITY_REQUIRED")
    if (
        str(company.get("stockCode", "")).strip() != code
        or str(company.get("market", "")).strip().upper() != market
        or str(company.get("displayName", "")).strip() != name
        or company.get("instrumentType") != stock["instrumentType"]
        or company.get("currency") != stock["currency"]
    ):
        raise StockAddWriterError("RESEARCH_PACKAGE_IDENTITY_MISMATCH")
    if (
        readback["status"] not in {"MATCH_FOUND", "NO_MATCH_CONFIRMED"}
        or readback["complete"] is not True
    ):
        raise StockAddWriterError("MASTER_READBACK_NOT_COMPLETE")
    if readback["environment"] != "PRODUCTION_READ_ONLY":
        raise StockAddWriterError("MASTER_READBACK_NOT_PRODUCTION")
    if not isinstance(readback["source"], str) or not readback["source"].strip():
        raise StockAddWriterError("MASTER_READBACK_SOURCE_REQUIRED")
    try:
        read_at = datetime.fromisoformat(str(readback["readAt"]).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise StockAddWriterError("MASTER_READBACK_TIME_INVALID") from exc
    if read_at.tzinfo is None or read_at.utcoffset() != timedelta(0):
        raise StockAddWriterError("MASTER_READBACK_TIME_MUST_BE_UTC")
    _require_sha256(readback["sha256"], "masterReadback.sha256")
    age = datetime.now(UTC) - read_at.astimezone(UTC)
    if age < timedelta(0) or age > timedelta(minutes=15):
        raise StockAddWriterError("MASTER_READBACK_STALE")

    prepared_package = prepare_research_publication(research_package)
    if prepared_package is None:
        raise StockAddWriterError("RESEARCH_PACKAGE_NOT_PUBLICATION_AUTHORIZED")
    if prepared_package != research_package:
        raise StockAddWriterError("RESEARCH_PACKAGE_POLICY_ATTESTATION_NOT_SEALED_IN_PLAN")
    try:
        project_approved_package(research_package)
    except ValueError as exc:
        raise StockAddWriterError(str(exc)) from exc
    metadata = research_package.get("researchMetadata")
    if not isinstance(metadata, dict):
        raise StockAddWriterError("RESEARCH_AS_OF_REQUIRED")
    try:
        date.fromisoformat(str(metadata["researchAsOf"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise StockAddWriterError("RESEARCH_AS_OF_INVALID") from exc
    payload = {key: value for key, value in plan.items() if key != "planSha256"}
    digest = canonical_sha256(payload)
    if plan["planSha256"] != digest:
        raise StockAddWriterError("PLAN_SHA256_MISMATCH")
    operation_id = f"stock-add:master:{market}:{code}:{digest}"
    if len(operation_id) > 160:
        raise StockAddWriterError("OPERATION_ID_TOO_LONG")
    return payload, digest, operation_id


def expected_confirmation(market: str, stock_code: str, plan_sha256: str) -> str:
    return f"{APPLY_CONFIRMATION_PREFIX} {market} {stock_code} {plan_sha256}"


def verify_target(
    connection: Connection,
    *,
    database_url: str,
    expected_host: str,
    expected_database: str,
    expected_role: str,
    expected_migration_head: str = EXPECTED_MIGRATION_HEAD,
) -> None:
    parsed = urlsplit(database_url)
    if (parsed.hostname or "").lower() != expected_host.strip().lower():
        raise StockAddWriterError("DATABASE_HOST_MISMATCH")
    if parse_qs(parsed.query).get("sslmode", [None])[0] not in {"require", "verify-full"}:
        raise StockAddWriterError("DATABASE_SSL_MODE_REQUIRED")
    if parsed.path.lstrip("/") != expected_database:
        raise StockAddWriterError("DATABASE_NAME_IN_URL_MISMATCH")
    current_database, current_user = connection.execute(
        text("SELECT current_database(), current_user")
    ).one()
    if current_database != expected_database:
        raise StockAddWriterError("DATABASE_NAME_MISMATCH")
    if current_user != expected_role:
        raise StockAddWriterError("DATABASE_ROLE_MISMATCH")
    role = connection.execute(
        text(
            "SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, "
            "rolreplication, rolbypassrls, rolinherit "
            "FROM pg_roles WHERE rolname = current_user"
        )
    ).one()
    if role[0] is not True or any(role[1:6]) or role[6]:
        raise StockAddWriterError("WRITER_ROLE_FLAGS_TOO_BROAD")
    if connection.execute(
        text(
            "SELECT EXISTS (SELECT 1 FROM pg_auth_members "
            "WHERE member = (SELECT oid FROM pg_roles WHERE rolname = current_user))"
        )
    ).scalar_one():
        raise StockAddWriterError("WRITER_ROLE_MEMBERSHIP_NOT_ALLOWED")

    privilege_names = (
        ("schema", "public", "USAGE"),
        ("schema", "topicpilot", "USAGE"),
        ("schema", "topicpilot", "CREATE"),
        ("schema", "public", "CREATE"),
        ("table", "topicpilot.markets", "SELECT"),
        ("table", "topicpilot.markets", "INSERT"),
        ("table", "topicpilot.markets", "UPDATE"),
        ("table", "topicpilot.markets", "DELETE"),
        ("table", "topicpilot.instruments", "SELECT"),
        ("table", "topicpilot.instruments", "INSERT"),
        ("table", "topicpilot.instruments", "UPDATE"),
        ("table", "topicpilot.instruments", "DELETE"),
        ("table", "topicpilot.instruments", "TRUNCATE"),
        ("table", "topicpilot.stock_add_operations", "SELECT"),
        ("table", "topicpilot.stock_add_operations", "INSERT"),
        ("table", "topicpilot.stock_add_operations", "UPDATE"),
        ("table", "topicpilot.stock_add_operations", "DELETE"),
        ("table", "topicpilot.stock_add_operations", "TRUNCATE"),
        ("table", "topicpilot.stock_add_operation_events", "SELECT"),
        ("table", "topicpilot.stock_add_operation_events", "INSERT"),
        ("table", "topicpilot.stock_add_operation_events", "UPDATE"),
        ("table", "topicpilot.stock_add_operation_events", "DELETE"),
        ("table", "topicpilot.stock_add_operation_events", "TRUNCATE"),
        ("table", "topicpilot.company_research_publications", "SELECT"),
        ("table", "topicpilot.company_research_publications", "INSERT"),
        ("table", "topicpilot.company_research_publications", "UPDATE"),
        ("table", "topicpilot.company_research_publications", "DELETE"),
        ("table", "topicpilot.company_research_publications", "TRUNCATE"),
        ("table", "public.alembic_version", "SELECT"),
        ("table", "public.alembic_version", "INSERT"),
        ("table", "public.alembic_version", "UPDATE"),
        ("table", "public.alembic_version", "DELETE"),
        ("table", "topicpilot.topics", "SELECT"),
        ("table", "topicpilot.topics", "INSERT"),
        ("table", "topicpilot.topics", "UPDATE"),
        ("table", "topicpilot.topics", "DELETE"),
        ("table", "topicpilot.topics", "TRUNCATE"),
        ("table", "topicpilot.instrument_topic_relations", "SELECT"),
        ("table", "topicpilot.instrument_topic_relations", "INSERT"),
        ("table", "topicpilot.instrument_topic_relations", "UPDATE"),
        ("table", "topicpilot.instrument_topic_relations", "DELETE"),
        ("table", "topicpilot.instrument_topic_relations", "TRUNCATE"),
    )
    privilege_query = ", ".join(
        f"has_schema_privilege(current_user, :object_{index}, :privilege_{index})"
        if kind == "schema"
        else f"has_table_privilege(current_user, :object_{index}, :privilege_{index})"
        for index, (kind, _, _) in enumerate(privilege_names)
    )
    privilege_params = {
        parameter: value
        for index, (_, object_name, privilege) in enumerate(privilege_names)
        for parameter, value in (
            (f"object_{index}", object_name),
            (f"privilege_{index}", privilege),
        )
    }
    privilege_rows = connection.execute(text(f"SELECT {privilege_query}"), privilege_params).one()
    expected_privileges = tuple(
        (kind, object_name, privilege)
        in {
            ("schema", "public", "USAGE"),
            ("schema", "topicpilot", "USAGE"),
            ("table", "topicpilot.markets", "SELECT"),
            ("table", "topicpilot.instruments", "SELECT"),
            ("table", "topicpilot.instruments", "INSERT"),
            ("table", "topicpilot.stock_add_operations", "SELECT"),
            ("table", "topicpilot.stock_add_operations", "INSERT"),
            ("table", "topicpilot.stock_add_operation_events", "SELECT"),
            ("table", "topicpilot.stock_add_operation_events", "INSERT"),
            ("table", "topicpilot.company_research_publications", "SELECT"),
            ("table", "topicpilot.company_research_publications", "INSERT"),
            ("table", "public.alembic_version", "SELECT"),
        }
        for kind, object_name, privilege in privilege_names
    )
    if tuple(privilege_rows) != expected_privileges:
        raise StockAddWriterError("WRITER_PRIVILEGES_OUTSIDE_APPROVED_WRITE_SET")
    heads = list(
        connection.execute(text("SELECT version_num FROM public.alembic_version")).scalars()
    )
    if heads != [expected_migration_head]:
        raise StockAddWriterError("MIGRATION_HEAD_MISMATCH")


def _existing_instrument(connection: Connection, market: str, code: str):
    return (
        connection.execute(
            text(
                "SELECT i.id, i.name, i.instrument_type, i.currency, i.valid_from, i.is_active "
                "FROM topicpilot.instruments AS i "
                "JOIN topicpilot.markets AS m ON m.id = i.market_id "
                "WHERE m.code = :market AND i.instrument_code = :code"
            ),
            {"market": market, "code": code},
        )
        .mappings()
        .first()
    )


def _verify_existing_identity(existing, stock: dict[str, Any]) -> None:
    if not existing["is_active"]:
        raise StockAddWriterError("MASTER_INSTRUMENT_INACTIVE")
    if (
        existing["name"] != stock["name"]
        or existing["instrument_type"] != stock["instrumentType"]
        or existing["currency"] != stock["currency"]
    ):
        raise StockAddWriterError("EXISTING_MASTER_IDENTITY_CONFLICT")


def _publication_by_package(connection: Connection, instrument_id, package_sha256: str):
    return (
        connection.execute(
            text(
                "SELECT id, publication_version, public_payload_sha256 "
                "FROM topicpilot.company_research_publications "
                "WHERE instrument_id = :instrument_id "
                "AND source_package_sha256 = :package_sha256"
            ),
            {"instrument_id": instrument_id, "package_sha256": package_sha256},
        )
        .mappings()
        .first()
    )


def _next_publication_version(connection: Connection, instrument_id) -> int:
    current = connection.execute(
        text(
            "SELECT COALESCE(MAX(publication_version), 0) "
            "FROM topicpilot.company_research_publications "
            "WHERE instrument_id = :instrument_id"
        ),
        {"instrument_id": instrument_id},
    ).scalar_one()
    return int(current) + 1


def dry_run_master_add(connection: Connection, plan: dict[str, Any]) -> StockAddMasterResult:
    payload, digest, operation_id = validate_master_plan(plan)
    market = plan["stock"]["market"].strip().upper()
    code = plan["stock"]["stockCode"].strip()
    stock = plan["stock"]
    package = plan["researchPackage"]
    package_sha256 = canonical_sha256(package)
    public_payload = project_approved_package(package).model_dump(by_alias=True, mode="json")
    public_payload_sha256 = canonical_sha256(public_payload)
    existing = _existing_instrument(connection, market, code)
    readback_status = payload["masterReadback"]["status"]
    if existing is not None:
        if readback_status != "MATCH_FOUND":
            raise StockAddWriterError("MASTER_MATCH_APPEARED_AFTER_NO_MATCH_READBACK")
        _verify_existing_identity(existing, stock)
        instrument_id = existing["id"]
        action = "PUBLISH_RESEARCH_UPDATE"
    else:
        if readback_status != "NO_MATCH_CONFIRMED":
            raise StockAddWriterError("MASTER_MATCH_MISSING_AFTER_MATCH_READBACK")
        if stock["validFrom"] is None or stock["validFromEvidenceUrl"] is None:
            raise StockAddWriterError("OFFICIAL_VALID_FROM_REQUIRED_FOR_NEW_INSTRUMENT")
        market_row = connection.execute(
            text("SELECT id FROM topicpilot.markets WHERE code = :market AND is_active"),
            {"market": market},
        ).first()
        if market_row is None:
            raise StockAddWriterError("MARKET_NOT_PRESENT_OR_INACTIVE")
        instrument_id = canonical_instrument_id(market, code)
        action = "ADD_INSTRUMENT_AND_PUBLISH"
    publication = _publication_by_package(connection, instrument_id, package_sha256)
    if publication is not None:
        if publication["public_payload_sha256"] != public_payload_sha256:
            raise StockAddWriterError("EXISTING_RESEARCH_PUBLICATION_HASH_CONFLICT")
        publication_version = int(publication["publication_version"])
        status = "DRY_RUN_ALREADY_PUBLISHED"
    else:
        publication_version = _next_publication_version(connection, instrument_id)
        status = (
            "DRY_RUN_RESEARCH_UPDATE_READY"
            if existing is not None
            else "DRY_RUN_ADD_AND_PUBLISH_READY"
        )
    return StockAddMasterResult(
        status=status,
        operation_id=operation_id,
        plan_sha256=digest,
        market=market,
        stock_code=code,
        instrument_id=str(instrument_id),
        created=False,
        publication_version=publication_version,
        action=action,
        publication_authorization=publication_authorization_summary(package),
    )


def apply_master_add(
    connection: Connection,
    plan: dict[str, Any],
    *,
    confirmation: str,
    operator: str,
) -> StockAddMasterResult:
    """Add a missing master row or publish a research update, atomically."""

    payload, digest, operation_id = validate_master_plan(plan)
    stock = plan["stock"]
    package = plan["researchPackage"]
    readback = payload["masterReadback"]
    market = stock["market"].strip().upper()
    code = stock["stockCode"].strip()
    package_sha256 = canonical_sha256(package)
    public_response = project_approved_package(package)
    authorization = publication_authorization_summary(package)
    if authorization is None:
        raise StockAddWriterError("RESEARCH_PACKAGE_NOT_PUBLICATION_AUTHORIZED")
    public_payload = public_response.model_dump(by_alias=True, mode="json")
    public_payload_sha256 = canonical_sha256(public_payload)
    research_as_of = date.fromisoformat(package["researchMetadata"]["researchAsOf"])
    if confirmation.strip() != expected_confirmation(market, code, digest):
        raise StockAddWriterError("FINAL_CONFIRMATION_HASH_MISMATCH")
    if not operator.strip():
        raise StockAddWriterError("OPERATOR_REQUIRED")

    connection.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:market), hashtext(:code))"),
        {"market": market, "code": code},
    )
    prior = (
        connection.execute(
            text(
                "SELECT operation_id, plan_sha256 FROM topicpilot.stock_add_operations "
                "WHERE operation_id = :operation_id"
            ),
            {"operation_id": operation_id},
        )
        .mappings()
        .first()
    )
    if prior is not None:
        if prior["plan_sha256"] != digest:
            raise StockAddWriterError("OPERATION_PLAN_HASH_MISMATCH")
        event = connection.execute(
            text(
                "SELECT artifact_sha256 FROM topicpilot.stock_add_operation_events "
                "WHERE operation_id = :operation_id "
                "AND stage = 'RESEARCH_DATA_PUBLISHED' AND status = 'PASS'"
            ),
            {"operation_id": operation_id},
        ).first()
        master_event = connection.execute(
            text(
                "SELECT artifact_sha256 FROM topicpilot.stock_add_operation_events "
                "WHERE operation_id = :operation_id "
                "AND stage = 'MASTER_DATA_VERIFIED' AND status = 'PASS'"
            ),
            {"operation_id": operation_id},
        ).first()
        existing = _existing_instrument(connection, market, code)
        publication = (
            _publication_by_package(connection, existing["id"], package_sha256)
            if existing is not None
            else None
        )
        if (
            event is None
            or event["artifact_sha256"] != digest
            or master_event is None
            or master_event["artifact_sha256"] != digest
            or existing is None
        ):
            raise StockAddWriterError("INCOMPLETE_OR_CONFLICTING_PRIOR_OPERATION")
        _verify_existing_identity(existing, stock)
        if publication is None or publication["public_payload_sha256"] != public_payload_sha256:
            raise StockAddWriterError("INCOMPLETE_OR_CONFLICTING_PRIOR_PUBLICATION")
        if readback["status"] == "NO_MATCH_CONFIRMED" and existing["valid_from"] is None:
            raise StockAddWriterError("PRIOR_ADD_VALID_FROM_MISSING")
        return StockAddMasterResult(
            status="NOOP_ALREADY_VERIFIED",
            operation_id=operation_id,
            plan_sha256=digest,
            market=market,
            stock_code=code,
            instrument_id=str(existing["id"]),
            created=False,
            publication_version=int(publication["publication_version"]),
            action=(
                "PUBLISH_RESEARCH_UPDATE"
                if readback["status"] == "MATCH_FOUND"
                else "ADD_INSTRUMENT_AND_PUBLISH"
            ),
            publication_authorization=authorization,
        )

    existing = _existing_instrument(connection, market, code)
    created = existing is None
    if existing is not None:
        if readback["status"] != "MATCH_FOUND":
            raise StockAddWriterError("MASTER_MATCH_APPEARED_AFTER_NO_MATCH_READBACK")
        _verify_existing_identity(existing, stock)
        instrument_id = existing["id"]
    else:
        if readback["status"] != "NO_MATCH_CONFIRMED":
            raise StockAddWriterError("MASTER_MATCH_MISSING_AFTER_MATCH_READBACK")
        if stock["validFrom"] is None or stock["validFromEvidenceUrl"] is None:
            raise StockAddWriterError("OFFICIAL_VALID_FROM_REQUIRED_FOR_NEW_INSTRUMENT")
        market_row = connection.execute(
            text("SELECT id FROM topicpilot.markets WHERE code = :market AND is_active"),
            {"market": market},
        ).first()
        if market_row is None:
            raise StockAddWriterError("MARKET_NOT_PRESENT_OR_INACTIVE")
        instrument_id = canonical_instrument_id(market, code)
        connection.execute(
            text(
                "INSERT INTO topicpilot.instruments "
                "(id, market_id, instrument_code, name, instrument_type, currency, "
                "valid_from, is_active) "
                "VALUES (:id, :market_id, :code, :name, :instrument_type, :currency, "
                ":valid_from, true)"
            ),
            {
                "id": instrument_id,
                "market_id": market_row[0],
                "code": code,
                "name": stock["name"],
                "instrument_type": stock["instrumentType"],
                "currency": stock["currency"],
                "valid_from": date.fromisoformat(stock["validFrom"]),
            },
        )

    publication = _publication_by_package(connection, instrument_id, package_sha256)
    if publication is not None:
        if publication["public_payload_sha256"] != public_payload_sha256:
            raise StockAddWriterError("EXISTING_RESEARCH_PUBLICATION_HASH_CONFLICT")
        publication_version = int(publication["publication_version"])
    else:
        publication_version = _next_publication_version(connection, instrument_id)
        connection.execute(
            text(
                "INSERT INTO topicpilot.company_research_publications "
                "(id, instrument_id, market_code, instrument_code, publication_version, "
                "research_as_of, source_package_sha256, public_payload_sha256, "
                "public_payload, published_by) "
                "VALUES (:id, :instrument_id, :market, :code, :version, :research_as_of, "
                ":package_sha256, :payload_sha256, CAST(:public_payload AS jsonb), :operator)"
            ),
            {
                "id": uuid4(),
                "instrument_id": instrument_id,
                "market": market,
                "code": code,
                "version": publication_version,
                "research_as_of": research_as_of,
                "package_sha256": package_sha256,
                "payload_sha256": public_payload_sha256,
                "public_payload": json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                "operator": operator.strip(),
            },
        )

    audit_payload = {
        "schemaVersion": PLAN_SCHEMA,
        "market": market,
        "stockCode": code,
        "action": "ADD_INSTRUMENT_AND_PUBLISH" if created else "PUBLISH_RESEARCH_UPDATE",
        "researchAsOf": research_as_of.isoformat(),
        "sourcePackageSha256": package_sha256,
        "publicPayloadSha256": public_payload_sha256,
        "masterReadbackSha256": readback["sha256"],
        "publicationVersion": publication_version,
        "publicationAuthorization": authorization,
    }
    connection.execute(
        text(
            "INSERT INTO topicpilot.stock_add_operations "
            "(operation_id, market_code, instrument_code, plan_sha256, payload, created_by) "
            "VALUES (:operation_id, :market, :code, :digest, CAST(:payload AS jsonb), :operator)"
        ),
        {
            "operation_id": operation_id,
            "market": market,
            "code": code,
            "digest": digest,
            "payload": json.dumps(audit_payload, ensure_ascii=False, sort_keys=True),
            "operator": operator.strip(),
        },
    )
    connection.execute(
        text(
            "INSERT INTO topicpilot.stock_add_operation_events "
            "(id, operation_id, stage, status, artifact_sha256, detail) "
            "VALUES (:id, :operation_id, 'MASTER_DATA_VERIFIED', 'PASS', :digest, "
            "CAST(:detail AS jsonb))"
        ),
        {
            "id": uuid4(),
            "operation_id": operation_id,
            "digest": digest,
            "detail": json.dumps(
                {
                    "instrumentId": str(instrument_id),
                    "market": market,
                    "stockCode": code,
                    "action": "INSTRUMENT_ADDED" if created else "IDENTITY_MATCH_CONFIRMED",
                },
                sort_keys=True,
            ),
        },
    )
    connection.execute(
        text(
            "INSERT INTO topicpilot.stock_add_operation_events "
            "(id, operation_id, stage, status, artifact_sha256, detail) "
            "VALUES (:id, :operation_id, 'RESEARCH_DATA_PUBLISHED', 'PASS', :digest, "
            "CAST(:detail AS jsonb))"
        ),
        {
            "id": uuid4(),
            "operation_id": operation_id,
            "digest": digest,
            "detail": json.dumps(
                {
                    "instrumentId": str(instrument_id),
                    "market": market,
                    "stockCode": code,
                    "publicationVersion": publication_version,
                    "publicPayloadSha256": public_payload_sha256,
                },
                sort_keys=True,
            ),
        },
    )
    return StockAddMasterResult(
        status="MASTER_ADDED_AND_RESEARCH_PUBLISHED" if created else "RESEARCH_UPDATED",
        operation_id=operation_id,
        plan_sha256=digest,
        market=market,
        stock_code=code,
        instrument_id=str(instrument_id),
        created=created,
        publication_version=publication_version,
        action=("ADD_INSTRUMENT_AND_PUBLISH" if created else "PUBLISH_RESEARCH_UPDATE"),
        publication_authorization=authorization,
    )
