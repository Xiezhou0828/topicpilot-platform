from __future__ import annotations

from ..contracts import EvaluationBundle
from .context import build_context
from .contracts import FeatureResult, FeatureStatus


def hierarchy_features(bundle: EvaluationBundle) -> tuple[FeatureResult, ...]:
    context = build_context(bundle)
    return tuple(
        FeatureResult(
            "hierarchy_quality",
            "v1",
            topic_id,
            bundle.as_of,
            FeatureStatus.INVALID_INPUT if flags else FeatureStatus.READY,
            {
                "descendant_count": len(context.descendants.get(topic_id, ())),
                "quality_flag_count": len(flags),
            },
            None,
            tuple(sorted(flags)),
        )
        for topic_id in context.topic_ids
        for flags in (context.flags.get(topic_id, ()),)
    )
