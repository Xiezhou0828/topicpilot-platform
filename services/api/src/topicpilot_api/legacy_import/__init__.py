"""V1-to-V2 legacy import contracts and planning primitives.

This package deliberately contains no source connector and no database writer.
It is the reviewable foundation for a later, separately authorized import run.
"""

from .contracts import (
    ImportBatch,
    ImportEntity,
    ImportManifest,
    ImportMode,
    ImportSource,
    Lineage,
)
from .dry_run import DryRunReport, validate_dry_run
from .export_contract import (
    ExportArtifact,
    ExportManifest,
    build_manifest,
    canonical_record_hash,
    parse_delimited,
)
from .mapping import (
    DEFAULT_MAPPING_POLICY,
    FieldMapping,
    MappingPolicy,
    MappingRule,
    UnsupportedFieldPolicy,
)
from .pipeline import ImportPlan, LegacyImportPipeline
from .validation import ValidationIssue, ValidationSeverity, validate_batch
from .writer import ImportConflict, TransactionalV2Writer

__all__ = [
    "DEFAULT_MAPPING_POLICY",
    "DryRunReport",
    "ExportArtifact",
    "ExportManifest",
    "FieldMapping",
    "ImportBatch",
    "ImportConflict",
    "ImportEntity",
    "ImportManifest",
    "ImportMode",
    "ImportPlan",
    "ImportSource",
    "LegacyImportPipeline",
    "Lineage",
    "MappingPolicy",
    "MappingRule",
    "TransactionalV2Writer",
    "UnsupportedFieldPolicy",
    "ValidationIssue",
    "ValidationSeverity",
    "build_manifest",
    "canonical_record_hash",
    "parse_delimited",
    "validate_batch",
    "validate_dry_run",
]
