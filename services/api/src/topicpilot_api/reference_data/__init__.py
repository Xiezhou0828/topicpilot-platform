"""Canonical reference bundle contracts for the reference-only bootstrap."""

from .bundle import (
    BUNDLE_FILE_NAMES,
    BundleValidationError,
    ReferenceBundle,
    build_bundle_from_sources,
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
    "BUNDLE_FILE_NAMES",
    "TRANSITION_KIND",
    "TRANSITION_WRITE_SET",
    "BundleValidationError",
    "ReferenceBundle",
    "ReferenceRegistryTransitionResult",
    "build_bundle_from_sources",
    "derive_transition_version",
    "load_bundle",
    "transition_reference_registry",
    "validate_bundle",
    "write_bundle",
]
