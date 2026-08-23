# Strength contract alternatives

## Comparison

| Alternative | Shape | Explainability | Data demand | Lifecycle independence | Historical reconstructability | Frontend usability | WS3 research usability | Overfitting risk | Leader-proxy risk | Disposition |
|---|---|---|---|---|---|---|---|---|---|---|
| **A** | Raw evidence vector only; grouped dimensions, no levels | Highest; every value traces to an existing evidence field | Lowest; current shadow fields plus explicit quality | Highest; no new stage rule | Highest among candidates; raw values can be replayed when inputs exist | Moderate; UI must show values/status rather than a badge | Highest; preserves continuous features and missingness | Lowest | Lowest if proxy is labelled | **Recommend V0** |
| **B** | Dimension labels: participation/intensity/persistence each Weak/Normal/Strong | Good when labels are backed by an approved policy; otherwise opaque | Medium/high; needs cut points, missing-data policy, classifier/version, and historical validation | Medium; labels can accidentally reuse Lifecycle cutoffs | Medium; labels are reconstructable only after policy and PIT inputs are frozen | High; easy to render dimension chips | Good for stratification, but loses information versus raw vector | Medium/high | Medium/high for Intensity if proxy drives label | **Deferred candidate V1** |
| **C** | Overall ordinal level: Weak/Normal/Strong/Very Strong | Lowest without an explicit aggregation explanation | Highest; needs cross-dimension normalization, missing-dimension rules, threshold policy, and validation | Lowest; likely to become a hidden stage/score substitute | Lowest; missing Persistence and proxy ambiguity make replay unstable | Highest superficially; one badge hides mixed evidence | Risky; encourages strategy conditioning before validation | Highest | Highest; one proxy can dominate | **Reject/defer V0** |

## A — Raw evidence vector only

A is the only option that can be defined safely from the current evidence
without inventing a new threshold family. It preserves positive breadth,
strong breadth, weak ratio, average change, and proxy-labelled leader change as
raw values, and keeps stage/candidate timing in a separate Lifecycle context
object. It also allows WS3 to test continuous effects, nonlinearities, and
missingness without pretending that a human-readable label is already
validated.

The trade-off is a less decorative frontend. That is acceptable: the frontend
can display concise raw evidence with an explicit `SHADOW`, `PROVISIONAL`, or
`UNAVAILABLE` state and should not manufacture a strength badge for
completeness.

## B — Dimension-level labels

B is a sensible future presentation contract after a separate Strength policy
exists. It must not copy the current Lifecycle policy thresholds. For example,
`positiveBreadth >= 0.70` is a Lifecycle candidate ingredient today, not
evidence that `Participation=STRONG` for a separate domain. B also needs a
clear decision on how to label a mixed vector such as high positive breadth,
low average change, and unavailable persistence.

Until historical validation exists, B should be represented only as a
research hypothesis or `PROVISIONAL` output, never as a production field.

## C — Overall ordinal level

C is deferred because it forces an aggregation problem before the evidence is
ready. It would need normalization across different units, a rule for
unavailable Persistence, a rule for proxy-led Intensity, and a policy for
conflicting dimensions. A hidden weighted sum would be a 0–100 score in all
but name. C is therefore rejected for V0 even if it would be the easiest UI.

## Decision

Adopt **A** for the research contract. Keep B as a future, separately
versioned dimension-label candidate. Keep C and any 0–100 total score
deferred until a pre-registered historical validation proves incremental
information value and an Owner approves a new policy.
