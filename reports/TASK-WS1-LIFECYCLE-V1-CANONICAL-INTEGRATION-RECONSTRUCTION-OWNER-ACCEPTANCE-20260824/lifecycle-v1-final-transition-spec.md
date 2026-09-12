# Lifecycle V1 final transition specification

The five stages remain `SPROUTING`, `FERMENTING`, `MAIN_RISE`, `MATURE`, and `DECLINING`.

Identity-aware evidence uses Lead/Core authority at 70% and Related at 30%. Related-only and Leader-only rallies cannot establish `MAIN_RISE`; broad Core activation can establish it without strong Lead confirmation. `MAIN_RISE` uses persistent state memory, segment metadata, running peak/anchor, meaningful-expansion clock, drawdown, and trajectory recovery.

`MAIN_RISE -> MATURE` requires five trading sessions without meaningful Lead/Core expansion and without meaningful trajectory recovery. `MATURE -> MAIN_RISE` is a valid direct re-entry and increments the segment. `MATURE -> DECLINING` requires identity-aware Lead/Core deterioration together with participation deterioration.

The reconstruction uses the implementation's final locked versions:

- Policy: `topic-lifecycle-policy.v1`
- Calculation: `topic-lifecycle-v1-shadow.v1`

The earlier `topic-lifecycle-policy.provisional.1` and old L5 artifact were not modified. No Strength score, ranking tier, or Strong/Weak label was created.
