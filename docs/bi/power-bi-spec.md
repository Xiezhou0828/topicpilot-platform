# Power BI implementation specification

## Objective

Create a portfolio-quality Power BI report that proves the same governed SQL
analytics contract can serve a React application and a business-intelligence
consumer. Power BI is a downstream analysis surface; it does not replace
PostgreSQL, FastAPI, or the React public demo.

## Tooling limitation

Power BI Desktop is required to create, refresh, inspect, and validate a `.pbix`
file. The current repository automation cannot produce or truthfully validate a
native `.pbix`. Therefore this work order delivers the data contract, model,
measures, report specification, review checklist, and required export artifacts.
A `.pbix` is accepted only after a maintainer opens it in Power BI Desktop and
completes the checks below.

## Data source modes

### Public portfolio mode

Use a committed synthetic CSV/Parquet export generated from the five approved
views, or connect to a disposable synthetic Neon branch with a read-only role.
The published `.pbix`, screenshots, and PDF must contain synthetic data only.

### Private development mode

Connect to a private PostgreSQL database with a read-only BI role. Never commit
credentials, private extracts, cached formal data, or a `.pbix` containing such
data. Private reports are not public portfolio artifacts.

## Approved source views

| View | Expected grain | Report use |
|---|---|---|
| `vw_latest_stock_snapshot` | One row per active stock at latest approved date | Stock overview and freshness |
| `vw_topic_constituents` | One row per active stock-topic relation | Topic composition and drill-through |
| `vw_topic_rotation_14d` | One topic summary over up to 14 available observations | Rotation rank and heating/cooling |
| `vw_strategy_performance` | Strategy run by horizon | KPI, comparison, sample quality |
| `vw_data_quality_daily` | Date by severity/event aggregate | Reliability and freshness page |

Do not reproduce strategy scoring or topic-state business rules in DAX. SQL
views own those definitions. DAX may implement presentation measures such as
formatted percentages, selected-period changes, and display warnings.

## Semantic model

Use a star-like model:

- `DimDate`: distinct latest/run/data dates from view extracts.
- `DimStock`: distinct stock identifiers and labels.
- `DimTopic`: distinct topic slugs and labels.
- `DimStrategy`: exactly `MAS`, `MAV`, `TMC`, `BB`, `PB`, `KD`.
- Facts: latest stock snapshot, topic rotation, topic constituents, strategy
  performance, and data-quality daily.

Relationships should be single-direction from dimensions to facts. Avoid
many-to-many except the explicit stock-topic bridge represented by
`vw_topic_constituents`. Mark `DimDate` as the date table when using import
mode. Preserve SQL `NULL` as Power BI blank; never replace blank with zero
unless a measure explicitly describes that choice.

## Required report pages

### 1. Executive overview

- Latest data date and bundle/freshness status.
- Active stocks/topics and six-strategy availability.
- Count of error/warning quality events.
- Synthetic-data banner visible without interaction.

### 2. Topic rotation (14 trading days)

- Ranked bar or quadrant for latest score and 14-observation score change.
- Current grade/state, coverage, constituent count, and available point count.
- Topic group and latest-date slicers.
- Tooltip distinguishing missing value from numeric zero.

### 3. Strategy performance

- Strategy/horizon comparison for sample count, win rate, and average return.
- Conditional formatting only when `status` indicates metric availability.
- Warning when sample count is below a documented display threshold.
- Drill-through to strategy/date context where available.

### 4. Data quality and freshness

- Daily severity counts and stable event-code breakdown.
- Latest import/data dates and stale/unavailable indicators.
- Table of public-safe quality messages with entity type/key.

### 5. Stock-topic relationships

- Topic-to-stock drill-down using the relation bridge.
- Filters for relation type, market, industry, topic group, and active/enabled.
- Current stock observation from `vw_latest_stock_snapshot`.

## Suggested measures

Names are part of the report contract; formulas must be reviewed against actual
view columns in Power BI Desktop.

- `[Active Stocks]`
- `[Enabled Topics]`
- `[Latest Data Date]`
- `[Data Age Days]`
- `[Selected Strategy Samples]`
- `[Win Rate %]`
- `[Average Return %]`
- `[Quality Error Count]`
- `[Quality Warning Count]`
- `[Topic Score Change 14D]`
- `[Coverage %]`

Percentage measures must not divide by zero and should return blank for missing
or unavailable status.

## Visual and accessibility rules

- Keep a persistent “Synthetic demonstration data” label.
- Do not use red/green as the sole encoding; add text/icon/state labels.
- Include descriptive titles, alt text, and keyboard-accessible slicers.
- Display the data date and freshness on every page.
- Limit precision to what the source contract supports.
- Do not imply a buy/sell recommendation or projected return.

## Required deliverables

After Power BI Desktop implementation, provide:

```text
portfolio/power-bi/
├─ TopicPilot-Synthetic.pbix
├─ TopicPilot-Synthetic.pdf
├─ README.md
├─ screenshots/
│  ├─ overview.png
│  ├─ topic-rotation.png
│  ├─ strategy-performance.png
│  ├─ data-quality.png
│  └─ stock-topic.png
└─ exports/
   ├─ vw_latest_stock_snapshot.csv
   ├─ vw_topic_constituents.csv
   ├─ vw_topic_rotation_14d.csv
   ├─ vw_strategy_performance.csv
   └─ vw_data_quality_daily.csv
```

Do not commit these files until the public-data review approves their content
and repository size. Large `.pbix` binaries may instead be attached to a tagged
release with checksum and license notice.

## Desktop validation checklist

- [ ] Open without credential prompts for the synthetic import-mode artifact.
- [ ] Refresh succeeds against a clean synthetic source or documented extracts.
- [ ] Data model contains only the approved views/dimensions.
- [ ] No hidden query contains a private host, username, path, token, or formal
      data source.
- [ ] SQL `NULL` remains blank through the model and visuals.
- [ ] All five pages, slicers, drill-through, and tooltips function.
- [ ] Totals match direct SQL validation queries for a selected date/topic/
      strategy/horizon.
- [ ] Synthetic-data and freshness labels appear on every page.
- [ ] PDF export and five required screenshots are visually reviewed.
- [ ] `.pbix` properties, recent sources, cached previews, and parameters contain
      no private data.
- [ ] SHA-256 and Power BI Desktop version are recorded in the artifact README.

## Acceptance

`PLATFORM-BI-001` documentation is complete when the five view definitions and
this implementation contract are reviewable. The report itself passes only
after Power BI Desktop validation, required screenshots/PDF/exports exist, and
all public-data/security checks are signed off. Documentation alone must never
claim that a `.pbix` was generated or validated.
