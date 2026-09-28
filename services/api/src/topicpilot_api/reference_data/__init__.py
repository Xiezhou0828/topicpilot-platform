"""Canonical reference bundle contracts for the reference-only bootstrap."""

from .bundle import (
    BUNDLE_DIR,
    BUNDLE_FILE_NAMES,
    BUNDLE_NAME,
    BundleValidationError,
    ReferenceBundle,
    build_bundle_from_sources,
    canonical_bundle_version,
    load_bundle,
    validate_bundle,
    write_bundle,
)
from .transition import (
    TRANSITION_KIND,
    TRANSITION_WRITE_SET,
    ReferenceRegistryTransitionResult,
    derive_transition_version,
    transition_reference_registry,
)

__all__ = [
    "BUNDLE_DIR",
    "BUNDLE_FILE_NAMES",
    "BUNDLE_NAME",
    "TRANSITION_KIND",
    "TRANSITION_WRITE_SET",
    "BundleValidationError",
    "ReferenceBundle",
    "ReferenceRegistryTransitionResult",
    "build_bundle_from_sources",
    "canonical_bundle_version",
    "derive_transition_version",
    "load_bundle",
    "transition_reference_registry",
    "validate_bundle",
    "write_bundle",
]
