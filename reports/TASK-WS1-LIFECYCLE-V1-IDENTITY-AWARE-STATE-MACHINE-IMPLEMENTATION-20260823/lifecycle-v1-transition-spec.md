# Lifecycle V1 Transition Specification

## Evidence topology

For each eligible Topic×Date, valid canonical member observations are partitioned by formal structural role. Lead means `REPRESENTATIVE`; Core means `CORE`; Related means `RELATED`. Unknown or missing role authority is fail-closed for V1 stage promotion.

The authority breadth is `0.70 × Lead/Core positive breadth + 0.30 × Related positive breadth`. The 70/30 value is evidence weighting, not a score and not a Strength label.

## Stage semantics

- **SPROUTING**: local early activation; a Lead/role-aware leader can qualify. Leader-only and Related-only activity stays here and cannot enter Main Rise.
- **FERMENTING**: Core resonance plus expanding participation and minimum Lead/Core intensity. It is not Main Rise.
- **MAIN_RISE**: requires a Core gate, Lead/Core participation, Lead/Core intensity, and the broad authority evidence gate. Related-only evidence cannot qualify.
- **MATURE**: from Main Rise after five trading sessions without meaningful Lead/Core expansion and without meaningful recovery. A one-day pullback alone does not mature the topic.
- **DECLINING**: only from Mature after dual confirmation: Lead/Core group drawdown is approximately `-8%` or worse from the persisted running peak and Lead/Core participation deteriorates. Confirmation requires two trading sessions.

## Main Rise memory

Every Main Rise entry starts a segment. Re-entry from Mature increments the segment. Each result carries entry date, anchor date, running peak references, days since meaningful expansion, drawdown, and the evidence used to update the state.

Meaningful expansion is Lead/Core close progression of at least 4% over the persisted member peak together with minimum Core/Lead-Core participation. Related-only highs do not reset the expansion clock.

## Confirmation and safety

Ordinary transitions require two matching candidate sessions. Main Rise→Mature is the explicit five-session stall transition. No V1 branch introduces a new stage, lowers minimum coverage, bypasses identity authority, or performs a production write.
