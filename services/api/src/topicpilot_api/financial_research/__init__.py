"""Non-production financial research foundation primitives.

The package deliberately has no ORM tables or migration dependency yet.  It
provides versioned contracts, source/normalization helpers, validation and a
read-only readiness surface so the persistence and publication decisions can
be made separately.
"""

from .contract import (
    FinancialCoverageResponse,
    FinancialFact,
    FinancialFiling,
    FinancialResearchStatusResponse,
    FinancialSource,
    FinancialStatementResponse,
    FinancialSummaryResponse,
    FinancialValidationReceipt,
    RawFinancialRecord,
)

__all__ = [
    "FinancialCoverageResponse",
    "FinancialFact",
    "FinancialFiling",
    "FinancialResearchStatusResponse",
    "FinancialSource",
    "FinancialStatementResponse",
    "FinancialSummaryResponse",
    "FinancialValidationReceipt",
    "RawFinancialRecord",
]
