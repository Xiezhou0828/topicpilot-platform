from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..contracts import EvaluationBundle


@dataclass(frozen=True)
class MembershipContext:
    topic_ids: tuple[str, ...]
    members: dict[str, frozenset[str]]
    descendants: dict[str, frozenset[str]]
    observed: frozenset[tuple[str, str]]
    flags: dict[str, frozenset[str]]

    def members_for(self, topic_id: str) -> frozenset[str]:
        ids = {topic_id, *self.descendants.get(topic_id, frozenset())}
        return frozenset(
            instrument for current in ids for instrument in self.members.get(current, ())
        )

    def observed_for(self, topic_id: str) -> frozenset[str]:
        ids = {topic_id, *self.descendants.get(topic_id, frozenset())}
        return frozenset(instrument for current, instrument in self.observed if current in ids)


def build_context(bundle: EvaluationBundle) -> MembershipContext:
    topic_ids = tuple(sorted({str(topic["id"]) for topic in bundle.topics if "id" in topic}))
    known = set(topic_ids)
    flags: dict[str, set[str]] = defaultdict(set)
    children: dict[str, set[str]] = defaultdict(set)
    for edge in bundle.hierarchy:
        parent, child = str(edge.get("parent_id")), str(edge.get("child_id"))
        if parent not in known or child not in known:
            owner = parent if parent in known else child
            if owner in known:
                flags[owner].add("MISSING_HIERARCHY_REFERENCE")
        elif parent == child:
            flags[parent].add("HIERARCHY_CYCLE")
        else:
            children[parent].add(child)
    descendants: dict[str, frozenset[str]] = {}
    for topic_id in topic_ids:
        found: set[str] = set()
        stack = list(sorted(children[topic_id], reverse=True))
        while stack:
            child = stack.pop()
            if child in found:
                flags[topic_id].add("HIERARCHY_CYCLE")
                continue
            found.add(child)
            stack.extend(sorted(children[child], reverse=True))
        descendants[topic_id] = frozenset(found)
    members: dict[str, set[str]] = defaultdict(set)
    for relation in bundle.memberships:
        topic, instrument = str(relation.get("topic_id")), str(relation.get("instrument_id"))
        if topic in known and instrument not in {"None", ""}:
            members[topic].add(instrument)
    observed = frozenset(
        (str(row.get("topic_id")), str(row.get("instrument_id"))) for row in bundle.observations
    )
    return MembershipContext(
        topic_ids,
        {k: frozenset(v) for k, v in members.items()},
        descendants,
        observed,
        {k: frozenset(v) for k, v in flags.items()},
    )
