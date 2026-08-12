"""Flush-only persistence boundary around the pure mapper."""

from sqlalchemy import and_, exists, select
from sqlalchemy.orm import Session

from topicpilot_api.orm.models import (
    CanonicalObservation,
    CanonicalPriceObservation,
    CanonicalQuoteObservation,
    CanonicalTradingStatusObservation,
    CanonicalVolumeObservation,
    ObservationTimelineEntry,
)

from .contracts import NormalizationResult, NormalizerMapper, ensure_utc, stable_hash
from .results import PersistedCanonicalReference, RuntimeResult

DETAILS = {
    "PRICE": CanonicalPriceObservation,
    "VOLUME": CanonicalVolumeObservation,
    "QUOTE": CanonicalQuoteObservation,
    "TRADING_STATUS": CanonicalTradingStatusObservation,
}
PERSISTABLE = {"ACCEPTED", "INCOMPLETE", "AMBIGUOUS", "CONFLICTING", "QUARANTINED"}


class NormalizationService:
    def __init__(self, session: Session, mapper: NormalizerMapper | None = None):
        self.session, self.mapper = session, mapper

    def persist(self, envelope, reference, policy, result: NormalizationResult):
        rows, existing, failures = [], [], list(result.failures)
        entry = self.session.get(ObservationTimelineEntry, envelope.timeline_entry_id)
        prior = {}
        if entry and entry.supersedes_id:
            successor = CanonicalObservation.__table__.alias("successor")
            all_prior = list(
                self.session.scalars(
                    select(CanonicalObservation).where(
                        CanonicalObservation.timeline_entry_id == entry.supersedes_id,
                        CanonicalObservation.quality_state == "ACCEPTED",
                    )
                )
            )
            candidate_families = {
                candidate.family_code
                for candidate in result.candidates
                if candidate.quality_state != "REJECTED"
            }
            branched = {
                row.family_code
                for row in all_prior
                if row.family_code in candidate_families
                and self.session.scalar(
                    select(
                        exists(
                            select(1)
                            .select_from(successor)
                            .where(
                                and_(
                                    successor.c.supersedes_id == row.id,
                                    successor.c.family_code == row.family_code,
                                    successor.c.quality_state == "ACCEPTED",
                                )
                            )
                        )
                    )
                )
            }
            if branched:
                raise RuntimeError(f"canonical supersession branch conflict: {sorted(branched)}")
            current = select(CanonicalObservation).where(
                CanonicalObservation.timeline_entry_id == entry.supersedes_id,
                CanonicalObservation.quality_state == "ACCEPTED",
                ~exists(
                    select(1)
                    .select_from(successor)
                    .where(
                        and_(
                            successor.c.supersedes_id == CanonicalObservation.id,
                            successor.c.family_code == CanonicalObservation.family_code,
                            successor.c.quality_state == "ACCEPTED",
                        )
                    )
                ),
            )
            prior_rows = list(self.session.scalars(current))
            if len({r.family_code for r in prior_rows}) != len(prior_rows):
                raise RuntimeError("canonical supersession branch conflict")
            for row in prior_rows:
                prior.setdefault(row.family_code, row)
        for candidate in result.candidates:
            if candidate.quality_state == "REJECTED" or candidate.quality_state not in PERSISTABLE:
                continue
            if candidate.quality_state == "QUARANTINED" and not policy.persist_quarantined:
                continue
            content = stable_hash(
                {
                    "family": candidate.family_code,
                    "values": candidate.values,
                    "paths": candidate.source_paths,
                }
            )
            idem = stable_hash(
                {
                    "entry": envelope.timeline_entry_id,
                    "family": candidate.family_code,
                    "content": content,
                    "contract": policy.normalization_contract_version,
                    "mapping": policy.mapping_policy_version,
                    "reference": reference.reference_data_version,
                }
            )
            found = self.session.scalar(
                select(CanonicalObservation).where(CanonicalObservation.idempotency_key == idem)
            )
            if found:
                existing_reference = PersistedCanonicalReference(
                    found.id,
                    found.family_code,
                    found.quality_state,
                    found.idempotency_key,
                    found.supersedes_id,
                    False,
                )
                existing.append(existing_reference)
                rows.append(existing_reference)
                continue
            row = CanonicalObservation(
                timeline_entry_id=envelope.timeline_entry_id,
                instrument_id=envelope.instrument_id,
                source_id=envelope.source_id,
                raw_observation_id=envelope.raw_observation_id,
                session_code=reference.session_code,
                timezone_name=reference.timezone_name,
                calendar_code=reference.calendar_code,
                family_code=candidate.family_code,
                observed_at=ensure_utc(envelope.observed_at),
                received_at=ensure_utc(envelope.received_at),
                retrieved_at=ensure_utc(envelope.retrieved_at),
                source_field_path=candidate.source_field_path,
                ordering_key=envelope.ordering_key,
                normalization_contract_version=policy.normalization_contract_version,
                mapping_policy_version=policy.mapping_policy_version,
                reference_data_version=reference.reference_data_version,
                quality_state=candidate.quality_state,
                quality_warnings={"warnings": candidate.warnings},
                validation_summary=candidate.validation,
                content_hash=content,
                idempotency_key=idem,
                supersedes_id=prior.get(candidate.family_code).id
                if candidate.family_code in prior
                else None,
            )
            self.session.add(row)
            self.session.flush()
            self.session.add(
                DETAILS[candidate.family_code](canonical_observation_id=row.id, **candidate.values)
            )
            rows.append(
                PersistedCanonicalReference(
                    row.id,
                    row.family_code,
                    row.quality_state,
                    row.idempotency_key,
                    row.supersedes_id,
                    True,
                )
            )
        self.session.flush()
        return RuntimeResult(result, tuple(rows), tuple(existing), tuple(failures))

    def normalize_and_persist(self, envelope, reference, policy):
        if self.mapper is None:
            raise ValueError("mapper is required for direct normalization")
        return self.persist(envelope, reference, policy, self.mapper(envelope, reference, policy))
