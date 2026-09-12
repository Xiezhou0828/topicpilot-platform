# Instrument + Topic Master V1

These three CSVs are the Owner-editable source of truth:

- `instruments.csv` — what canonical instruments exist. The stable identity
  key is `(market_code, instrument_code)`; an instrument may have no topic.
- `topics.csv` — what topics exist and how they nest.
- `instrument_topic_memberships.csv` — how instruments relate to topics,
  including relation type, LEAD/CORE/RELATED role, weight, and effective dates.

The initial seed preserves the research mapping as pending review and carries
the six currently known MLCC role rows without changing them. Run the
validator with all three files before review or canonical synchronization.
Generated snapshots and reference bundles are derived artifacts; do not edit
them manually.
