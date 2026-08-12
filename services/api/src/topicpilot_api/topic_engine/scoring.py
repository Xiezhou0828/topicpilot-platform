from __future__ import annotations

from .contracts import EvaluationBundle, TopicState
from .features.context import build_context


def calculate_states(bundle: EvaluationBundle) -> tuple[TopicState, ...]:
    if not bundle.calculation_version.strip():
        raise ValueError("calculation_version must be non-empty")
    context = build_context(bundle)
    states = []
    for topic_id in context.topic_ids:
        all_members = context.members_for(topic_id)
        seen = context.observed_for(topic_id)
        coverage = len(seen) / len(all_members) if all_members else None
        flags = tuple(sorted(context.flags.get(topic_id, ())))
        status = (
            "INVALID_INPUT" if flags else ("DATA_INSUFFICIENT" if not seen else "READY_UNSCORED")
        )
        states.append(
            TopicState(
                topic_id,
                bundle.as_of,
                bundle.calculation_version,
                status,
                None,
                None,
                None,
                coverage,
                len(all_members),
                len(seen),
                flags,
            )
        )
    return tuple(states)
