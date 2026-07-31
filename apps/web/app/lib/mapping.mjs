export function nullableNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function nullableString(value) {
  if (value === null || value === undefined) return null;
  const text = String(value).trim();
  return text.length ? text : null;
}

export function readValue(source, ...keys) {
  for (const key of keys) {
    if (source && Object.prototype.hasOwnProperty.call(source, key)) return source[key];
  }
  return undefined;
}

export function unwrapItems(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  return [];
}

export function mapStock(raw) {
  const topicValue = readValue(raw, "topicNames", "topic_names", "topics");
  const topicNames = Array.isArray(topicValue)
    ? topicValue.map((item) => typeof item === "string" ? item : item?.name).filter(Boolean)
    : [];
  return {
    code: nullableString(readValue(raw, "code", "stock_code")) ?? "UNKNOWN",
    name: nullableString(readValue(raw, "name", "stock_name")) ?? "未命名標的",
    market: nullableString(readValue(raw, "market", "exchange")),
    group: nullableString(readValue(raw, "group", "major_group", "industry")),
    price: nullableNumber(readValue(raw, "price", "close_price", "close")),
    changePct: nullableNumber(readValue(raw, "changePct", "change_pct")),
    volumeRatio: nullableNumber(readValue(raw, "volumeRatio", "volume_ratio")),
    signal: nullableString(readValue(raw, "signal", "state", "technicalState", "technical_state")),
    topicNames,
    updatedAt: nullableString(readValue(raw, "updatedAt", "updated_at", "data_time", "dataDate", "data_date")),
  };
}

export function mapTopic(raw) {
  return {
    slug: nullableString(readValue(raw, "slug", "topic_slug")) ?? "unknown-topic",
    name: nullableString(readValue(raw, "name", "topic_name")) ?? "未命名題材",
    parentName: nullableString(readValue(raw, "parentName", "parent_name", "group", "groupName", "group_name")),
    grade: nullableString(readValue(raw, "grade", "child_grade")),
    score: nullableNumber(readValue(raw, "score", "strength_score")),
    change14d: nullableNumber(readValue(raw, "change14d", "change_14d", "change")),
    memberCount: nullableNumber(readValue(raw, "memberCount", "member_count", "observed_count", "constituentCount", "constituent_count")),
    state: nullableString(readValue(raw, "state", "strength_state", "strengthState", "signal")),
  };
}

export function mapStrategy(raw) {
  return {
    key: nullableString(readValue(raw, "key", "strategyKey", "strategy_key", "strategyId", "strategy_id")) ?? "MAS",
    name: nullableString(readValue(raw, "name", "strategy_name")) ?? "未命名策略",
    summary: nullableString(readValue(raw, "summary", "description")) ?? "尚未提供策略說明。",
    status: nullableString(readValue(raw, "status", "batch_status")),
    candidateCount: nullableNumber(readValue(raw, "candidateCount", "candidate_count")),
    dataDate: nullableString(readValue(raw, "dataDate", "data_date", "batch_date")),
  };
}

export function mapDataStatus(raw) {
  const source = raw?.data ?? raw ?? {};
  const counts = source.counts ?? source.rowCounts ?? source.row_counts ?? {};
  const quality = source.quality ?? source.data_quality ?? {};
  const bundleVersion = nullableString(readValue(source, "bundleVersion", "bundle_version", "contract_version"));
  const completedAt = nullableString(readValue(source, "completedAt", "completed_at"));
  return {
    dataDate: nullableString(readValue(source, "dataDate", "data_date")),
    updatedAt: nullableString(readValue(source, "updatedAt", "updated_at", "generatedAt", "generated_at", "completedAt", "completed_at")),
    bundleVersion,
    sourceMode: nullableString(readValue(source, "sourceMode", "source_mode", "sourceKind", "source_kind", "classification")),
    apiStatus: nullableString(readValue(source, "apiStatus", "api_status")) ?? (bundleVersion ? "healthy" : "unavailable"),
    databaseStatus: nullableString(readValue(source, "databaseStatus", "database_status")) ?? (completedAt ? "healthy" : "unavailable"),
    latencyMs: nullableNumber(readValue(source, "latencyMs", "latency_ms")),
    counts: {
      stocks: nullableNumber(readValue(counts, "stocks", "stock_count")),
      topics: nullableNumber(readValue(counts, "topics", "topic_count")),
      strategyCandidates: nullableNumber(readValue(counts, "strategyCandidates", "strategy_candidates", "candidate_count")),
    },
    quality: {
      passed: nullableNumber(readValue(quality, "passed", "passed_count")),
      warnings: nullableNumber(readValue(quality, "warnings", "warning_count")),
      failed: nullableNumber(readValue(quality, "failed", "failed_count")),
    },
  };
}
