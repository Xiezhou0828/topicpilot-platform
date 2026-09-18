"""Repository-authoritative governance identities.

This is provenance metadata, not authentication or RBAC.  The registry keeps
formal Owner identity stable across workstations, accounts, and agents while
making the authority represented by an identity explicit and queryable.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

GOVERNANCE_IDENTITY_SCHEMA_VERSION = "topicpilot-governance-identity.v1"
GOVERNANCE_OWNER_KIND = "GOVERNANCE_OWNER"
FORMAL_OWNER_ID = "topicpilot-owner"
FORMAL_OWNER_PRINCIPAL = f"{GOVERNANCE_OWNER_KIND}:{FORMAL_OWNER_ID}"


@dataclass(frozen=True)
class GovernanceIdentity:
    """Stable governance principal metadata; no login credential is implied."""

    identity_id: str
    kind: str
    authority: tuple[str, ...]
    credential: bool
    account_binding: str
    formal_decision_refs: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": GOVERNANCE_IDENTITY_SCHEMA_VERSION,
            "id": self.identity_id,
            "kind": self.kind,
            "authority": list(self.authority),
            "credential": self.credential,
            "accountBinding": self.account_binding,
            "formalDecisionRefs": list(self.formal_decision_refs),
        }


TOPICPILOT_OWNER: Final = GovernanceIdentity(
    identity_id=FORMAL_OWNER_ID,
    kind=GOVERNANCE_OWNER_KIND,
    authority=("PRODUCT_POLICY_APPROVAL", "FORMAL_GOVERNANCE_DECISION"),
    credential=False,
    account_binding="none",
    formal_decision_refs=("TOPIC_B2_LAYER2_POLICY_V1",),
)

GOVERNANCE_IDENTITY_REGISTRY: Final[Mapping[str, GovernanceIdentity]] = MappingProxyType(
    {FORMAL_OWNER_ID: TOPICPILOT_OWNER}
)


def resolve_governance_identity(identity_id: str) -> GovernanceIdentity | None:
    """Resolve one exact repository identity without accepting aliases."""

    return GOVERNANCE_IDENTITY_REGISTRY.get(identity_id)


def require_governance_identity(identity_id: str) -> GovernanceIdentity:
    """Return a registered identity or fail closed for an unknown key."""

    identity = resolve_governance_identity(identity_id)
    if identity is None:
        raise ValueError(f"UNKNOWN_GOVERNANCE_IDENTITY: {identity_id}")
    return identity


def resolve_governance_principal(principal: str) -> GovernanceIdentity | None:
    """Resolve a namespaced formal principal to its registered identity."""

    for prefix in ("OWNER:", "GOVERNANCE_OWNER:", "principal://"):
        if principal.startswith(prefix):
            identity_id = principal[len(prefix) :]
            identity = resolve_governance_identity(identity_id)
            if identity is not None and identity.kind == GOVERNANCE_OWNER_KIND:
                return identity
            return None
    return None


__all__ = [
    "FORMAL_OWNER_ID",
    "FORMAL_OWNER_PRINCIPAL",
    "GOVERNANCE_IDENTITY_REGISTRY",
    "GOVERNANCE_IDENTITY_SCHEMA_VERSION",
    "GOVERNANCE_OWNER_KIND",
    "TOPICPILOT_OWNER",
    "GovernanceIdentity",
    "require_governance_identity",
    "resolve_governance_identity",
    "resolve_governance_principal",
]
