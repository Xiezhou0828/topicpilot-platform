# PHASE-3.7-002D — Topic Formula Candidate Evidence

- **Generation:** `NEXT / V2`
- **Status:** `RESEARCH BASIS / NOT PRODUCT POLICY`
- **Purpose:** document primary-source support and limitations for research-only candidate mechanics.

## Primary sources

1. [OECD / EU / EC-JRC — Handbook on Constructing Composite Indicators (2008)](https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html) describes normalization, weighting, aggregation, robustness, and sensitivity analysis as distinct decisions in composite-indicator construction.
2. [OECD — Oslo Manual 2018, Chapter 11](https://www.oecd.org/en/publications/oslo-manual-2018_9789264304604-en/full-report/component-18.html) states that composite indicators normalize inputs to a common scale and may use identical or different weights, while warning that weights can be subjective and aggregation can hide detail.
3. [The Conference Board — How to Compute Diffusion Indexes](https://www.conference-board.org/data/bci/index.cfm?id=2180) defines a diffusion index by assigning increasing components `1`, unchanged components `0.5`, decreasing components `0`, averaging, and multiplying by `100`.
4. [Federal Reserve — Industrial Production and Capacity Utilization, G.17](https://www.federalreserve.gov/Releases/G17/20251223/g17.pdf) defines its diffusion indexes as the percentage of series that increased plus one-half the percentage that were unchanged.

## What the sources support

- A proportion of positively participating members is a transparent research representation of participation breadth when the upstream positive/neutral/negative classification is explicit.
- A diffusion variant that gives neutral observations one-half contribution is an established indicator mechanic and is suitable for comparison against a strict positive-only proportion.
- Breadth and Leadership inputs must be on a common declared scale before a composite aggregation is attempted.
- Weighting and aggregation assumptions must be explicit, versioned, and sensitivity-tested rather than presented as objective truth.

## What the sources do not support

- They do not prove that these mechanics predict Taiwan equity Topic behavior.
- They do not define TopicPilot's return window, positive/neutral cutoff, CORE derivation, Leader Set, freshness rule, eligibility cutoff, component weights, Grade thresholds, or production formula.
- Diffusion indexes in the cited sources describe economic/industrial series. Reusing the mechanic for Topic member participation is an explicit TopicPilot research hypothesis, not a source-backed production conclusion.
- An equal-weight arithmetic example is only a transparent baseline. It is not evidence that Breadth and Leadership have equal economic importance.

## Authorized candidate hypotheses

| Candidate mechanic | Research question | Production status |
|---|---|---|
| Strict participation proportion | Does the share of explicitly positive members provide a stable component? | Not authorized |
| Diffusion participation proportion | Does half-credit for neutral members reduce instability without hiding deterioration? | Not authorized |
| Explicit weighted arithmetic aggregation | How sensitive is the composite result to declared Breadth/Leadership trade-offs? | Not authorized; no default weights |

## Required future evidence

Before any promotion decision, candidates require point-in-time historical member/leader sets, explicit observation windows and classification rules, survivorship-safe replay, data-coverage reporting, sensitivity analysis across weights and cutoffs, and evaluation against subsequent Topic behavior. Candidate comparison must report uncertainty and failure modes; it must not select a winner from the synthetic corpus.
