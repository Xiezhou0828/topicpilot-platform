from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .contracts import ImportBatch, ImportEntity, ImportManifest, ImportMode
from .mapping import DEFAULT_MAPPING_POLICY, MappingPolicy
from .validation import ValidationIssue, validate_batch


class LegacyReader(Protocol):
    def read(self, entity: ImportEntity) -> ImportBatch: ...


class V2Writer(Protocol):
    def apply(self, batch: ImportBatch, policy: MappingPolicy) -> None: ...


@dataclass(frozen=True)
class ImportPlan:
    mode: ImportMode
    manifest: ImportManifest
    issues: tuple[ValidationIssue, ...]

    @property
    def ready_to_apply(self) -> bool:
        return self.mode == ImportMode.APPLY and not any(i.severity == "ERROR" for i in self.issues)


class LegacyImportPipeline:
    """Orchestrates validation and future application without owning I/O."""

    def __init__(self, policy: MappingPolicy = DEFAULT_MAPPING_POLICY) -> None:
        self.policy = policy

    def plan(
        self,
        batches: list[ImportBatch],
        manifest: ImportManifest,
        mode: ImportMode = ImportMode.VALIDATE_ONLY,
    ) -> ImportPlan:
        issues: list[ValidationIssue] = []
        for batch in batches:
            issues.extend(validate_batch(batch.entity.value, list(batch.records), self.policy))
        return ImportPlan(mode=mode, manifest=manifest, issues=tuple(issues))

    def apply(self, plan: ImportPlan, writer: V2Writer, batches: list[ImportBatch]) -> None:
        if not plan.ready_to_apply:
            raise ValueError(
                "Import plan is not ready to apply; resolve validation errors and use APPLY mode"
            )
        for batch in batches:
            writer.apply(batch, self.policy)
