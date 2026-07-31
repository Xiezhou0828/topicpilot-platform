from __future__ import annotations

from typing import Final

CONTRACT_VERSION: Final = "enterprise_bundle.v1"
SNAPSHOT_VERSION: Final = "enterprise-db-001"

STRATEGY_KEYS: Final[tuple[str, ...]] = ("MAS", "MAV", "TMC", "BB", "PB", "KD")
STRATEGY_NAMES: Final[dict[str, str]] = {
    "MAS": "Moving Average Strength",
    "MAV": "Moving Average Volume",
    "TMC": "Topic Momentum Confirmation",
    "BB": "Breakout Base",
    "PB": "Pullback",
    "KD": "KD Recovery",
}
STRATEGY_HORIZONS: Final[tuple[str, ...]] = (
    "T+1",
    "T+3",
    "T+5",
    "T+10",
    "T+20",
    "T+30",
)
