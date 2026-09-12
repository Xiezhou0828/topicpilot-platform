"""Atomic, immutable reference-registry version rollover contract.

The canonical bundle may keep its source ``referenceDataVersion`` while its
content evolves. A rollover gives that content a deterministic registry
version derived from the source version and full bundle digest. The previous
registry row and all of its context rows remain intact and are linked to the
new row by an append-only transition provenance record.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from topicpilot_api.orm.models import ReferenceRegistrySet, ReferenceRegistryTransition

from .bootstrap import (
    NON_REFERENCE_WRITE_SET,
    REFERENCE_WRITE_SET,
    ReferenceBootstrapConflict,
    ReferenceBootstrapResult,
    _validate_registry_rows,
    bootstrap_reference_bundle,
)
from .bundle import ReferenceBundle, validate_bundle

TRANSITION_KIND = "BUNDLE_ROLLOVER"
REFERENCE_VERSION_MAX_LENGTH = 64
_ROLLOVER_VERSION_RE = re.compile(r"(?P<family>.+)-rollover-[0-9a-f]{16}$")
_ROLLOVER_DIGEST_LENGTH = 16
_COMPACT_FAMILY_PREFIX_LENGTH = 20
_COMPACT_DIGEST_LENGTH = 32
TRANSITION_WRITE_SET = frozenset(
    {*REFERENCE_WRITE_SET, "reference_registry_transitions"}
)


@dataclass(frozen=True)
class ReferenceRegistryTransitionResult:
    operation: str
    from_reference_data_version: str
    to_reference_data_version: str
    from_bundle_sha256: str | None
    to_bundle_sha256: str
    status: str
    dry_run: bool
    created_markets: int
    created_instruments: int
    created_reference_rows: int
    noop_reference_rows: int
    retired_registry_sets: int
    old_registry_preserved: bool
    transition_recorded: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "fromReferenceVersion": self.from_reference_data_version,
            "toReferenceVersion": self.to_reference_data_version,
            "fromBundleSha256": self.from_bundle_sha256,
            "toBundleSha256": self.to_bundle_sha256,
            "status": self.status,
            "dryRun": self.dry_run,
            "createdMarkets": self.created_markets,
            "createdInstruments": self.created_instruments,
            "createdReferenceRows": self.created_reference_rows,
            "noopReferenceRows": self.noop_reference_rows,
            "retiredRegistrySets": self.retired_registry_sets,
            "oldRegistryPreserved": self.old_registry_preserved,
            "transitionRecorded": self.transition_recorded,
            "writeSet": sorted(TRANSITION_WRITE_SET),
            "nonReferenceWriteSet": sorted(NON_REFERENCE_WRITE_SET),
            "transactional": True,
            "idempotent": True,
            "sameVersionHashOverwrite": False,
            "singleActiveRegistry": True,
        }


def derive_transition_version(source_version: str, bundle_sha256: str) -> str:
    """Return a deterministic, bounded successor version for a bundle rollover.

    Existing first-generation rollover names remain unchanged. A generated
    rollover suffix is parsed back to its stable family before deriving the
    next target, so repeated transitions do not grow without bound. Long
    families use a deterministic compact form that still binds the complete
    family and bundle hash.
    """

    if not source_version or len(source_version) > REFERENCE_VERSION_MAX_LENGTH:
        raise ReferenceBootstrapConflict("source reference version is invalid")
    if len(bundle_sha256) != 64 or any(char not in "0123456789abcdef" for char in bundle_sha256):
        raise ReferenceBootstrapConflict("bundle hash is invalid")

    rollover_match = _ROLLOVER_VERSION_RE.fullmatch(source_version)
    family = rollover_match.group("family") if rollover_match else source_version
    target = f"{family}-rollover-{bundle_sha256[:_ROLLOVER_DIGEST_LENGTH]}"
    if len(target) > REFERENCE_VERSION_MAX_LENGTH:
        safe_prefix = re.sub(r"[^A-Za-z0-9_-]+", "-", family).strip("-_")
        safe_prefix = safe_prefix[:_COMPACT_FAMILY_PREFIX_LENGTH] or "reference"
        identity = f"{family}\0{bundle_sha256}".encode()
        compact_digest = hashlib.sha256(identity).hexdigest()[:_COMPACT_DIGEST_LENGTH]
        target = f"{safe_prefix}-r-{compact_digest}"
    if len(target) > REFERENCE_VERSION_MAX_LENGTH:
        raise ReferenceBootstrapConflict("derived transition reference version is too long")
    return target


def _transition_bundle(bundle: ReferenceBundle, target_version: str) -> ReferenceBundle:
    manifest = dict(bundle.manifest)
    manifest["referenceDataVersion"] = target_version
    return replace(bundle, manifest=manifest)


def _registry_for_version(
    session: Session,
    version: str,
    *,
    for_update: bool,
) -> ReferenceRegistrySet | None:
    statement = select(ReferenceRegistrySet).where(
        ReferenceRegistrySet.reference_data_version == version
    )
    if for_update:
        statement = statement.with_for_update()
    rows = list(session.scalars(statement))
    if len(rows) > 1:
        raise ReferenceBootstrapConflict(f"reference version is duplicated: {version}")
    return rows[0] if rows else None


def _transition_record(
    session: Session,
    *,
    from_registry_id,
    to_registry_id,
) -> ReferenceRegistryTransition | None:
    return session.scalar(
        select(ReferenceRegistryTransition).where(
            ReferenceRegistryTransition.from_registry_set_id == from_registry_id,
            ReferenceRegistryTransition.to_registry_set_id == to_registry_id,
        )
    )


def _result_from_bootstrap(
    result: ReferenceBootstrapResult,
    *,
    source: ReferenceRegistrySet,
    target_version: str,
    operation: str,
    retired_registry_sets: int,
    transition_recorded: bool,
    status: str | None = None,
) -> ReferenceRegistryTransitionResult:
    return ReferenceRegistryTransitionResult(
        operation=operation,
        from_reference_data_version=source.reference_data_version,
        to_reference_data_version=target_version,
        from_bundle_sha256=source.bundle_sha256,
        to_bundle_sha256=result.bundle_sha256,
        status=status or result.status,
        dry_run=result.dry_run,
        created_markets=result.created_markets,
        created_instruments=result.created_instruments,
        created_reference_rows=result.created_reference_rows,
        noop_reference_rows=result.noop_reference_rows,
        retired_registry_sets=retired_registry_sets,
        old_registry_preserved=True,
        transition_recorded=transition_recorded,
    )


def transition_reference_registry(
    session: Session,
    bundle: ReferenceBundle,
    *,
    from_reference_version: str,
    expected_from_bundle_sha256: str,
    activate: bool,
    dry_run: bool = False,
) -> ReferenceRegistryTransitionResult:
    """Plan or atomically activate a deterministic bundle registry rollover."""

    if activate == dry_run:
        raise ValueError("exactly one of activate or dry_run must be true")
    if not dry_run and session.in_transaction():
        raise RuntimeError("registry transition requires a fresh SQLAlchemy session")
    validate_bundle(bundle)
    source_version = bundle.manifest["referenceDataVersion"]
    if source_version != from_reference_version:
        raise ReferenceBootstrapConflict(
            "bundle source version does not match from-reference-version"
        )
    bundle_hash = bundle.digest()
    if expected_from_bundle_sha256 == bundle_hash:
        raise ReferenceBootstrapConflict(
            "same-version hash is unchanged; use reference bootstrap NOOP instead"
        )
    target_version = derive_transition_version(source_version, bundle_hash)
    target_bundle = _transition_bundle(bundle, target_version)

    source = _registry_for_version(session, source_version, for_update=False)
    if source is None:
        raise ReferenceBootstrapConflict("source reference version does not exist")
    if source.bundle_sha256 != expected_from_bundle_sha256:
        raise ReferenceBootstrapConflict("source registry bundle hash precondition failed")
    target = _registry_for_version(session, target_version, for_update=False)

    if target is not None and target.bundle_sha256 not in (None, bundle_hash):
        raise ReferenceBootstrapConflict("transition target version has a different bundle hash")
    if target is not None:
        record = _transition_record(
            session,
            from_registry_id=source.id,
            to_registry_id=target.id,
        )
        if target.status == "ACTIVE" and record is not None:
            _validate_registry_rows(session, target.id, target_bundle)
            return _result_from_bootstrap(
                ReferenceBootstrapResult(
                    "NOOP",
                    target_version,
                    bundle_hash,
                    "ACTIVE",
                    dry_run,
                    0,
                    0,
                    0,
                    0,
                    0,
                ),
                source=source,
                target_version=target_version,
                operation="NOOP",
                retired_registry_sets=0,
                transition_recorded=True,
            )
        if record is not None:
            raise ReferenceBootstrapConflict("transition target already has provenance")

    if source.status != "ACTIVE":
        raise ReferenceBootstrapConflict("source reference registry is not ACTIVE")

    if dry_run:
        planned = bootstrap_reference_bundle(
            session,
            target_bundle,
            activate=False,
            dry_run=True,
        )
        return _result_from_bootstrap(
            planned,
            source=source,
            target_version=target_version,
            operation="PLAN",
            retired_registry_sets=1,
            transition_recorded=False,
        )

    # The preflight SELECTs use SQLAlchemy's autobegin. They ran only after the
    # fresh-session check above, so discard that read transaction before owning
    # the one atomic mutation transaction below.
    session.rollback()
    with session.begin():
        source = _registry_for_version(session, source_version, for_update=True)
        if source is None or source.bundle_sha256 != expected_from_bundle_sha256:
            raise ReferenceBootstrapConflict("source registry changed before activation")
        if source.status != "ACTIVE":
            raise ReferenceBootstrapConflict("source reference registry is not ACTIVE")
        target = _registry_for_version(session, target_version, for_update=True)
        if target is not None and target.bundle_sha256 not in (None, bundle_hash):
            raise ReferenceBootstrapConflict(
                "transition target version has a different bundle hash"
            )
        if target is not None and _transition_record(
            session,
            from_registry_id=source.id,
            to_registry_id=target.id,
        ) is not None:
            raise ReferenceBootstrapConflict("transition has already been recorded")

        bootstrapped = bootstrap_reference_bundle(
            session,
            target_bundle,
            activate=False,
            _allow_existing_transaction=True,
        )
        target = _registry_for_version(session, target_version, for_update=True)
        if target is None:
            raise ReferenceBootstrapConflict("transition target registry was not created")
        _validate_registry_rows(session, target.id, target_bundle)

        active_sets = list(
            session.scalars(
                select(ReferenceRegistrySet)
                .where(ReferenceRegistrySet.status == "ACTIVE")
                .with_for_update()
            )
        )
        retired = 0
        for active in active_sets:
            if active.id != target.id:
                active.status = "RETIRED"
                retired += 1
        session.flush()
        target.status = "ACTIVE"
        session.flush()
        session.add(
            ReferenceRegistryTransition(
                from_registry_set_id=source.id,
                to_registry_set_id=target.id,
                from_reference_data_version=source.reference_data_version,
                to_reference_data_version=target.reference_data_version,
                from_bundle_sha256=source.bundle_sha256,
                to_bundle_sha256=target.bundle_sha256,
                transition_kind=TRANSITION_KIND,
            )
        )
        session.flush()
        return _result_from_bootstrap(
            bootstrapped,
            source=source,
            target_version=target_version,
            operation="TRANSITION_ACTIVATED",
            retired_registry_sets=retired,
            transition_recorded=True,
            status="ACTIVE",
        )


__all__ = [
    "NON_REFERENCE_WRITE_SET",
    "REFERENCE_VERSION_MAX_LENGTH",
    "REFERENCE_WRITE_SET",
    "TRANSITION_KIND",
    "TRANSITION_WRITE_SET",
    "ReferenceRegistryTransitionResult",
    "derive_transition_version",
    "transition_reference_registry",
]
