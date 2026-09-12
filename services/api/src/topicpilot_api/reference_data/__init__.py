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


def __getattr__(name: str):
    """Load database transition helpers only when a caller requests them.

    Offline bundle generation and validation must not require the optional ORM
    dependency merely because the reference-data package is imported.
    """

    transition_names = {
        "TRANSITION_KIND",
        "TRANSITION_WRITE_SET",
        "ReferenceRegistryTransitionResult",
        "derive_transition_version",
        "transition_reference_registry",
    }
    if name in transition_names:
        from . import transition

        value = getattr(transition, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
