# Strength dimension analysis

## Separation rule

Lifecycle answers **where the topic is in its diffusion/state process**. Strength
answers **how strong the currently observed state appears**. The same raw
observation can be evidence for both descriptions, but the contracts are not
the same: Strength is descriptive evidence and Lifecycle remains the sole
owner of stage semantics, transition confirmation, hysteresis, persistence,
and confidence behavior.

The current engine's evidence is the source of truth for this research:
`topic_lifecycle_engine.py` computes member-level valid changes, breadth,
average change, weak/strong classifications, and a role-aware-or-proxy
leader. The existing lifecycle spec says these values are shadow/provisional,
not a production Strength policy.

## Participation

### Evidence role

`positive_breadth` is the cleanest current participation fact: the share of
valid observed members with positive change. `strong_breadth` is related but
not independent: under the current classifier, strong members are a subset of
positive members. `weak_ratio` is counter-participation/weakness evidence, not
the mathematical complement of positive breadth because flat members and
missing members remain separate.

Recommended V0 vector:

```text
positiveBreadth: raw value
strongBreadth: raw value, with classifier version/status
weakRatio: raw value, with classifier version/status
```

Do not collapse these into a participation label. A high positive breadth with
low strong breadth is a different state from high positive and high strong
breadth; likewise, a low positive breadth with a high weak ratio is not simply
`WEAK` without a separately approved classifier and validation.

`coveragePct`, expected members, observed members, and valid changes are
required to interpret the denominator, but they are quality metadata. They do
not add market strength.

## Intensity

### Evidence role

`average_change_pct` is the primary group-level intensity fact. It describes
the equal-weight mean change over valid observed members and remains null when
there are no valid observations. `leader_change_pct` adds a peak/asymmetry
view, but its interpretation depends on leader semantics.

The current engine sets `leaderSemanticAvailable=false` when no accepted role
metadata is present and falls back to `maxObservedChange`. That value can be
useful as a shadow research feature, but it is not a formal Leader Set, not a
stable structural identity, and not an authority. `leader_id`,
`leader_role`, and `positiveContributionShare` should therefore be nested in
an explicitly labelled proxy object if exposed.

Recommended V0 vector:

```text
averageChangePct: raw group intensity
leaderProxy.changePct: raw peak intensity, nullable
leaderProxy.semanticAvailable: boolean
leaderProxy.method: maxObservedChange | roleAwareObservedChange | unavailable
leaderProxy.memberId: nullable context only
```

The proxy must never determine a new Lifecycle stage, override the existing
engine's policy, or be shown as a formal leader in Topic Detail.

## Persistence

### Evidence role

The engine has `stageTradingDays`, `stageEnteredAt`, previous stage, previous
candidate, candidate streak, and confirmation state. These are valuable
Lifecycle state/process facts, but they do not directly establish that
Strength has persisted. A topic can be in `MATURE` or `DECLINING` for many
days; a long stage age is not a `STRONG` label. A candidate streak can describe
pending Lifecycle confirmation while the topic's raw intensity is fading.

`recent breadth persistence` — for example, breadth over a bounded prior-N
trading-day window, streak count, or stability/dispersion — is not currently
available in a PIT-safe, versioned form. The V0 contract must expose it as
`UNAVAILABLE`, not zero, not false, and not a synthetic history.

Recommended V0 behavior:

- expose stage age and candidate streak under `persistence.context`;
- mark `persistence.strengthStatus = PROVISIONAL_CONTEXT_ONLY`;
- set `recentBreadthPersistence = null` with an explicit unavailable reason;
- do not emit a Persistence `WEAK/NORMAL/STRONG` label.

## Data quality and confidence

Quality is a gate on whether evidence deserves interpretation. It is not a
fourth Strength dimension and must not be included in a total score.

The quality envelope should carry coverage, expected/eligible/observed/valid
counts, sample confidence, coverage confidence, overall confidence, small
sample, data/evaluation status, evaluation mode, policy/calculation versions,
and lineage/finality where available. Missingness remains explicit. A highly
covered topic with small positive changes is not stronger merely because the
coverage is high; a low-coverage topic is not weaker merely because its
quality is poor.

## What is safe to derive later

The first derived layer that may be researched later is not an overall level;
it is dimension-specific descriptive summaries, each with a separately frozen
policy and a versioned status. Even then, labels must be validated within the
same Lifecycle stage and must preserve mixed profiles and unavailable
dimensions. Any derived label is downstream of raw evidence and quality gates;
it never becomes a replacement for raw evidence.
