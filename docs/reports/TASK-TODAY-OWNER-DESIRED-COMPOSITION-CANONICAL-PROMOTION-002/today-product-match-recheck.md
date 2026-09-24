# Today Owner-desired product-match recheck

```text
MARKET_OVERVIEW_SECTION=YES
TODAY_MARKET_FOCUS_SECTION=YES
TODAY_MAINLINE_SECTION=YES
TOP3_MAINLINE_CARDS=YES_WHERE_DATA_AVAILABLE
GRADE_BADGES=YES_WHERE_FORMALLY_AVAILABLE
TOPIC_NAVIGATION=YES
NUMERIC_01_02_03_LABELS=NO
REDUNDANT_SNAPSHOT_LABEL=NO
ENGINEERING_METADATA_DOMINANT=NO
FIRST_VIEWPORT_COMPACTNESS_STATUS=PASS
TODAY_OWNER_PRODUCT_MATCH_GATE=PASS
```

The final Today source keeps the required reading order:

1. `市場概況`
2. `今日市場重點`
3. `今日主線`

Mainline cards preserve backend order, use the canonical topic slug, and show a
formal grade badge only when the backend supplies a grade. The compact disclosure
keeps source, status, and freshness metadata secondary to investor-facing
content. No browser ranking, synthetic market fact, ordinal `01`/`02`/`03`
label, or redundant `盤中快照` label is introduced.

The local browser smoke ran without a FastAPI origin. It therefore correctly
showed explicit unavailable states instead of fabricated market values or
mainline cards. The candidate's focused Today tests cover the formal data
branch, including the three backend-ordered cards, conditional grades, topic
navigation, and partial-data semantics.
