from __future__ import annotations

from ..contracts import EvaluationBundle
from .context import build_context
from .contracts import FeatureResult, FeatureStatus


def availability_features(bundle: EvaluationBundle) -> tuple[FeatureResult, ...]:
    context = build_context(bundle)
    return tuple(
        FeatureResult(
            "observation_availability",
            "v1",
            topic_id,
            bundle.as_of,
            (
                FeatureStatus.INVALID_INPUT
                if context.flags.get(topic_id)
                else FeatureStatus.READY
                if available
                else FeatureStatus.DATA_INSUFFICIENT
            ),
            {"observation_present": available},
            None,
            tuple(sorted(context.flags.get(topic_id, ()))),
        )
        for topic_id in context.topic_ids
        for available in (bool(context.observed_for(topic_id)),)
    )
