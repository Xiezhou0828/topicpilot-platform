from __future__ import annotations

from ..contracts import EvaluationBundle
from .context import build_context
from .contracts import FeatureResult, FeatureStatus


def membership_features(bundle: EvaluationBundle) -> tuple[FeatureResult, ...]:
    context = build_context(bundle)
    results: list[FeatureResult] = []
    for topic_id in context.topic_ids:
        members = context.members_for(topic_id)
        observed = context.observed_for(topic_id)
        flags = tuple(sorted(context.flags.get(topic_id, ())))
        status = (
            FeatureStatus.INVALID_INPUT
            if flags
            else FeatureStatus.READY
            if observed
            else FeatureStatus.DATA_INSUFFICIENT
        )
        coverage = len(observed) / len(members) if members else None
        results.extend(
            (
                FeatureResult(
                    "membership_count",
                    "v1",
                    topic_id,
                    bundle.as_of,
                    status,
                    {
                        "direct_member_count": len(context.members.get(topic_id, ())),
                        "rolled_up_member_count": len(members),
                        "observed_member_count": len(observed),
                    },
                    coverage,
                    flags,
                ),
                FeatureResult(
                    "membership_coverage",
                    "v1",
                    topic_id,
                    bundle.as_of,
                    status,
                    coverage,
                    coverage,
                    flags,
                ),
            )
        )
    return tuple(results)
