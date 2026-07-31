// WEB-DATA-002 snapshot → 視圖模型的純函式 adapter。
// 原則：不做 I/O、不丟例外；缺欄位一律回 null，讓頁面用空狀態呈現而非崩潰。

import type {
  Freshness,
  HomeData,
  MarketIndexView,
  MarketRadarView,
  MarketDecisionView,
  ObservationRow,
  ObservationSummary,
  QualityView,
  RawIndex,
  RawObservation,
  RawSnapshot,
  RawStock,
  RawTopicRelation,
  RawTopicStrengthHistory,
  Stance,
  TopicGroupView,
  TopicView,
  WatchRow,
  WatchlistData,
  StockView,
  TopicRelationView,
  TopicStrengthHistoryView,
  RawRadarMetric,
  RawRadarRotationItem,
  RawMarketDecision,
  StrategyCandidateView,
  StrategyPerformanceView,
  StrategyRegistryView,
} from "./types";

function num(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const t = v.replace(/,/g, "").replace(/%/g, "").trim();
    if (t === "") return null;
    const n = Number(t);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

export function toTopicViews(raw: RawSnapshot): TopicView[] {
  return (raw.topics ?? []).map((topic): TopicView => ({
    name: str(topic.name) ?? "未命名題材",
    group: str(topic.group),
    type: str(topic.type),
    grade: str(topic.grade) ?? "觀察",
    childGrade: str(topic.childGrade),
    strengthState: str(topic.strengthState),
    confidence: str(topic.confidence),
    score: num(topic.score),
    strengthScore: num(topic.strengthScore) ?? num(topic.score),
    strengthSource: str(topic.strengthSource),
    calculationStatus: str(topic.calculationStatus),
    breadth: str(topic.breadth),
    breadthRatio: num(topic.breadthRatio),
    stockCount: num(topic.stockCount),
    observedCount: num(topic.observedCount),
    strongCount: num(topic.strongCount),
    weakCount: num(topic.weakCount),
    signal: str(topic.signal),
    leaders: Array.isArray(topic.leaders) ? topic.leaders.map(String) : [],
    relationCount: num(topic.relationCount),
    note: str(topic.note),
  }));
}

export function toTopicGroupViews(raw: RawSnapshot): TopicGroupView[] {
  return (raw.topicGroups ?? []).map((group): TopicGroupView => ({
    name: str(group.name) ?? "未分類",
    score: num(group.score),
    strengthState: str(group.strengthState),
    childCount: num(group.childCount),
    scoredChildCount: num(group.scoredChildCount),
    strongestChild: str(group.strongestChild),
    strongestChildScore: num(group.strongestChildScore),
    children: Array.isArray(group.children) ? group.children.map(String) : [],
  }));
}

function str(v: unknown): string | null {
  if (v === null || v === undefined) return null;
  const s = String(v).trim();
  return s === "" ? null : s;
}

function pick(obj: Record<string, unknown> | undefined, key: string): unknown {
  if (!obj) return undefined;
  return obj[key];
}

function pickFirst(obj: Record<string, unknown> | undefined, keys: string[]): unknown {
  for (const key of keys) {
    const value = pick(obj, key);
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return undefined;
}

function demandLower(technical: Record<string, unknown> | undefined): number | null {
  const d = pick(technical, "需求區");
  if (d && typeof d === "object") {
    return num((d as Record<string, unknown>)["下緣"]);
  }
  return null;
}

// snapshot 是否可用：需有 dailyObservation 或 stocks 有內容。
export function isSnapshotUsable(raw: RawSnapshot | null | undefined): boolean {
  if (!raw || typeof raw !== "object") return false;
  const hasObs = Array.isArray(raw.dailyObservation) && raw.dailyObservation.length > 0;
  const hasStocks = !!raw.stocks && Object.keys(raw.stocks).length > 0;
  return hasObs || hasStocks;
}

export function toStrategyRegistry(raw: RawSnapshot): StrategyRegistryView | null {
  const registry = raw.strategyRegistry;
  if (!registry || !Array.isArray(registry.strategies)) return null;
  return {
    version: str(registry.version),
    dataDate: str(registry.dataDate),
    strategies: registry.strategies.flatMap((item) => {
      const strategyId = str(item.strategyId);
      if (!strategyId) return [];
      return [{ strategyId, name: str(item.name) ?? strategyId, modelVersion: str(item.modelVersion), batchDate: str(item.batchDate), batchStatus: str(item.batchStatus), candidateCount: num(item.candidateCount), selectedCount: num(item.selectedCount), rankingCount: num(item.rankingCount), missingReason: str(item.missingReason) }];
    }),
  };
}

export function toStrategyCandidates(raw: RawSnapshot): StrategyCandidateView[] {
  return (raw.strategyCandidates ?? []).flatMap((item) => {
    const strategyId = str(item.strategyId);
    const code = str(item.code);
    if (!strategyId || !code) return [];
    return [{ strategyId, strategyKey: str(item.strategyKey), modelVersion: str(item.modelVersion), batchDate: str(item.batchDate), rank: num(item.rank), code, name: str(item.name), majorGroup: str(item.majorGroup), fineTopic: str(item.fineTopic), score: num(item.score), reason: str(item.reason), price: num(item.price), dataDate: str(item.dataDate), dataTime: str(item.dataTime), trigger: num(item.trigger), support: num(item.support), invalidation: num(item.invalidation) }];
  });
}

export function toStrategyPerformance(raw: RawSnapshot): StrategyPerformanceView[] {
  return (raw.strategyPerformance ?? []).flatMap((item) => {
    const strategyId = str(item.strategyId);
    if (!strategyId) return [];
    const horizons = Object.entries(item.horizons ?? {}).map(([horizon, value]) => ({ horizon, status: str(value?.status), sampleCount: num(value?.sampleCount), winRate: num(value?.winRate), returnPct: num(value?.returnPct) ?? num(value?.avgReturnPct), reason: str(value?.reason) }));
    return [{ strategyId, strategyKey: str(item.strategyKey), name: str(item.name), modelVersion: str(item.modelVersion), dataDate: str(item.dataDate), status: str(item.status), sampleCount: num(item.sampleCount), availableHorizonCount: num(item.availableHorizonCount), horizons, source: str(item.source) }];
  });
}

function fmtNumber(n: number | null): string {
  if (n === null) return "待接資料源";
  return n.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

function indexStance(env: string | null, slope: number | null): Stance {
  if (env && (env.includes("多") || env.includes("強"))) return "risk-on";
  if (env && (env.includes("空") || env.includes("弱"))) return "risk-off";
  if (slope !== null) return slope > 0 ? "risk-on" : slope < 0 ? "risk-off" : "neutral";
  return "neutral";
}

// 六大指數：加權（真實）＋其餘先標「待接資料源」，不硬編假數字（見 WEB_DATA_GAP_MAP.md）。
const INDEX_SLOTS = ["加權指數", "櫃買指數", "費半指數", "日經 225", "KOSPI", "Nasdaq"];

export function toMarketIndexViews(raw: RawSnapshot): MarketIndexView[] {
  const rawIndices: RawIndex[] = raw.market?.indices ?? [];
  const byName = new Map<string, RawIndex>();
  for (const idx of rawIndices) byName.set(idx.name, idx);

  return INDEX_SLOTS.map((name): MarketIndexView => {
    const found = byName.get(name);
    if (found) {
      const close = num(found.close);
      const slope = num(found["ma20Slope%"]);
      const env = str(found.env);
      const sub = env;
      return {
        name,
        value: fmtNumber(close),
        change: null, // market_context 目前無日漲跌%
        stance: indexStance(env, slope),
        pending: close === null,
        subLabel: sub,
        asOf: str(found.asOf),
      };
    }
    return {
      name,
      value: "待接資料源",
      change: null,
      stance: "neutral",
      pending: true,
      subLabel: null,
      asOf: null,
    };
  });
}

function subTypeOf(st: RawStock | undefined): string | null {
  const tech = st?.technical;
  const stage = str(pick(tech, "型態階段"));
  if (stage) return stage;
  return str(pick(tech, "RS狀態")) ?? str(pick(tech, "state"));
}

function obsNum(o: RawObservation, modernKey: keyof RawObservation, legacyKey: string): number | null {
  return num(o[modernKey]) ?? num((o as unknown as Record<string, unknown>)[legacyKey]);
}

function obsStr(o: RawObservation, modernKey: keyof RawObservation, legacyKey: string): string | null {
  return str(o[modernKey]) ?? str((o as unknown as Record<string, unknown>)[legacyKey]);
}

function fundingConfirmOf(st: RawStock | undefined): string | null {
  return str(pick(st?.chip, "資金確認燈號文字"));
}

function catalystOf(st: RawStock | undefined): string | null {
  return str(pick(st?.fundamental, "基本面催化燈號文字"));
}

function shortRiskOf(st: RawStock | undefined): string | null {
  const r = st?.risk;
  const text = str(pick(r, "主要風險")) ?? str(pick(r, "籌碼風險"));
  return text && !/暫無|無明顯/.test(text) ? text : null;
}

export function toObservationRows(raw: RawSnapshot): ObservationRow[] {
  const obs: RawObservation[] = raw.dailyObservation ?? [];
  const stocks = raw.stocks ?? {};
  return obs.map((o): ObservationRow => {
    const st = stocks[o.code];
    return {
      code: o.code,
      name: str(o.name) ?? str(st?.name),
      section: str(o.section) ?? str(o.setup),
      subType: str(o.technicalSubtype) ?? subTypeOf(st),
      price: obsNum(o, "price", "現價") ?? num(pickFirst(st?.price, ["現價", "close"])),
      change: num(pickFirst(st?.price, ["漲跌幅", "changePct"])),
      volume: num(pickFirst(st?.price, ["成交量", "volume"])),
      volumeRatio: num(pickFirst(st?.technical, ["量比", "5日均量倍數", "量能倍數", "成交量比"])),
      volumeStatus: str(pick(st?.technical, "量能狀態")),
      trigger: num(o.triggerValue) ?? obsNum(o, "trigger", "觸發價"),
      triggerLabel: str(o.triggerLabel) ?? obsStr(o, "trigger", "觸發價"),
      distance: obsNum(o, "distanceToTriggerPct", "距觸發價%"),
      entryScore: num(o.entryScore) ?? num(o.EntryScore),
      gate: obsStr(o, "gate", "Gate"),
      fundingConfirm: str(o.chipConfirmation) ?? fundingConfirmOf(st),
      fundamentalCatalyst: str(o.fundamentalCatalyst) ?? catalystOf(st),
      shortRisk: str(o.shortRisk) ?? shortRiskOf(st),
      watchDays: num(o.watchDays),
      dataFreshness: str(o.dataFreshness) ?? str(pick(st?.quality, "dataFreshness")) ?? str(pick(st?.risk, "dataFreshness")),
      exceptionMessage: str(o.exceptionMessage) ?? str(pick(st?.quality, "exceptionMessage")),
      updatedAt: str(o.updatedAt),
      topicRole: str(o.topicRole),
      topicDefinition: str(o.topicDefinition),
    };
  });
}

export function toWatchRows(raw: RawSnapshot): WatchRow[] {
  const base = toObservationRows(raw);
  const obs = raw.dailyObservation ?? [];
  const stocks = raw.stocks ?? {};
  return base.map((row, i): WatchRow => {
    const st = stocks[row.code];
    const entry = st?.entry;
    const o = obs[i];
    return {
      ...row,
      rank: num(o?.rank) ?? i + 1,
      topic: str(o?.topic),
      trigger: row.trigger ?? num(pick(entry, "觸發價")),
      distance: row.distance ?? num(pick(entry, "距觸發價%")),
      support: num(o?.supportValue) ?? num(o?.support) ?? num(pick(entry, "觀察支撐")) ?? demandLower(st?.technical),
      supportLabel: str(o?.supportLabel) ?? str(o?.support) ?? str(pick(entry, "觀察支撐")),
      resistance: num(o?.pressureValue) ?? num(o?.pressure) ?? num(pick(entry, "壓力價")),
      resistanceLabel: str(o?.pressureLabel) ?? str(o?.pressure) ?? str(pick(entry, "壓力價")),
      invalidation: num(o?.invalidationValue) ?? num(o?.invalid) ?? num(pick(entry, "失效價")),
      invalidationLabel: str(o?.invalidationLabel) ?? str(o?.invalid) ?? str(pick(entry, "失效價")),
      stopPct: num(o?.stopLossPct) ?? num(pick(entry, "停損幅度%")),
      gateReason: str(o?.gateReason) ?? str(pick(entry, "Gate 原因")),
      entrySetup: str(pick(entry, "Entry Setup")),
      suggestedAction: str(pick(entry, "建議動作")),
      foreignFlow: num(pick(st?.chip, "外資5日買超佔量%")),
      hasFunding: !!row.fundingConfirm,
      hasCatalyst: !!row.fundamentalCatalyst,
      hasRisk: !!row.shortRisk,
    };
  });
}

export function summarizeSections(rows: ObservationRow[]): ObservationSummary[] {
  const counts = new Map<string, number>();
  for (const r of rows) {
    const key = r.section ?? "未分段";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return Array.from(counts.entries()).map(([section, count]) => ({ section, count }));
}

export function toQualityView(raw: RawSnapshot): QualityView {
  const q = raw.quality;
  if (!q) return null;
  return {
    total: q.universe ?? 0,
    priceRows: q.priceRows ?? 0,
    technicalRows: q.technicalRows ?? 0,
    chipRows: q.chipRows ?? 0,
    fundamentalRows: q.fundamentalRows ?? 0,
    entryRows: q.entryRows ?? 0,
    missingChip: q.missingChip?.length ?? 0,
    missingFundamental: q.missingFundamental?.length ?? 0,
    missingEntry: q.missingEntry?.length ?? 0,
    unavailableTechnical: q.unavailableTechnicalFields ?? [],
    dailyObservationSource: str(q.dailyObservationSource),
    entrySource: str(q.entrySource),
  };
}

function completenessNote(raw: RawSnapshot): string {
  const q = raw.quality;
  if (!q) return "資料品質資訊待接";
  const parts: string[] = [];
  parts.push(`報價 ${q.priceRows ?? 0}`);
  parts.push(`技術 ${q.technicalRows ?? 0}`);
  parts.push((q.chipRows ?? 0) > 0 ? `籌碼 ${q.chipRows}` : "籌碼待接");
  parts.push((q.fundamentalRows ?? 0) > 0 ? `基本面 ${q.fundamentalRows}` : "基本面待接");
  parts.push((q.entryRows ?? 0) > 0 ? `Gate ${q.entryRows}` : "Gate待接");
  return parts.join("、");
}

// 掃描 stocks，取某一群組（chip/fundamental）某欄的第一個非空值，作為該類資料的代表日期。
function firstStockField(raw: RawSnapshot, group: "chip" | "fundamental", key: string): string | null {
  const stocks = raw.stocks ?? {};
  for (const code of Object.keys(stocks)) {
    const g = stocks[code]?.[group];
    if (g) {
      const v = str(g[key]);
      if (v) return v;
    }
  }
  return null;
}

function firstPriceField(raw: RawSnapshot, keys: string[]): string | null {
  const stocks = raw.stocks ?? {};
  for (const code of Object.keys(stocks)) {
    const value = str(pickFirst(stocks[code]?.price, keys));
    if (value) return value;
  }
  return null;
}

// 觀察列資料新鮮度：任何一列被標記為非 CURRENT 即視為有過舊資料（僅提示，不改排序）。
function stalenessOf(raw: RawSnapshot): { stale: boolean; reason: string | null } {
  const obs = raw.dailyObservation ?? [];
  let staleCount = 0;
  for (const o of obs) {
    const f = str(o.dataFreshness);
    if (f && f.toUpperCase() !== "CURRENT") staleCount += 1;
  }
  if (staleCount === 0) return { stale: false, reason: null };
  return { stale: true, reason: `${staleCount} 檔資料標記為非最新，請確認資料時間` };
}

export function toFreshness(raw: RawSnapshot): Freshness {
  const dataDate = str(raw.quoteMeta?.dataDate) ?? str(raw.dataDate);
  const staleness = stalenessOf(raw);
  const synthetic = raw.classification === "PUBLIC_SYNTHETIC" || /synthetic|portfolio demo/i.test(str(raw.quoteMeta?.source) ?? "");
  return {
    snapshotVersion: str(raw.snapshotVersion),
    dataDate,
    generatedAt: str(raw.generatedAt),
    completeness: completenessNote(raw),
    note: raw.quality ? null : "資料品質資訊待接",
    sourceLabel: synthetic ? "公開合成資料" : "FastAPI / PostgreSQL read model",
    priceAsOf: dataDate,
    quoteUpdatedAt: str(raw.quoteMeta?.updatedAt) ?? firstPriceField(raw, ["更新時間", "updatedAt"]),
    quoteSource: str(raw.quoteMeta?.source) ?? firstPriceField(raw, ["資料來源", "source"]),
    quoteStatus: str(raw.quoteMeta?.status),
    latestTradingDate: str(raw.marketSession?.latestTradingDate),
    marketSession: str(raw.marketSession?.session),
    marketSessionReason: str(raw.marketSession?.reason),
    technicalAsOf: dataDate,
    institutionalAsOf: firstStockField(raw, "chip", "資料日期"),
    tdccAsOf: firstStockField(raw, "chip", "大戶資料日期"),
    fundamentalYm: firstStockField(raw, "fundamental", "資料年月"),
    stale: staleness.stale,
    staleReason: staleness.reason,
  };
}

export function buildHomeFromSnapshot(raw: RawSnapshot): HomeData {
  const rows = toObservationRows(raw);
  return {
    source: "snapshot",
    freshness: toFreshness(raw),
    quality: toQualityView(raw),
    marketIndices: toMarketIndexViews(raw),
    observation: {
      total: rows.length,
      asOf: str(raw.dataDate),
      summary: summarizeSections(rows),
      completenessNote: completenessNote(raw),
    },
    preview: rows,
  };
}

export function buildWatchlistFromSnapshot(raw: RawSnapshot): WatchlistData {
  const rows = toWatchRows(raw);
  const sections = Array.from(new Set(rows.map((r) => r.section ?? "未分段")));
  return {
    source: "snapshot",
    freshness: toFreshness(raw),
    quality: toQualityView(raw),
    rows,
    sections,
  };
}

function relationView(relation: RawTopicRelation | Record<string, unknown>): TopicRelationView | null {
  const item = relation as Record<string, unknown>;
  const code = str(pickFirst(item, ["股號", "code", "stockCode"]));
  const topic = str(pickFirst(item, ["題材", "topic", "fineTopic", "topicName", "name"]));
  if (!code || !topic) return null;
  return {
    code,
    name: str(pickFirst(item, ["名稱", "name", "stockName"])),
    topic,
    role: str(pickFirst(item, ["題材角色", "role", "relationType"])),
    type: str(pickFirst(item, ["題材類型", "type"])),
    parentGroup: str(pickFirst(item, ["主大族群", "parentGroup", "groupName"])),
    relatedGroup: str(pickFirst(item, ["關聯大族群", "relatedGroup"])),
    relation: str(pickFirst(item, ["關係", "relation", "relationType"])),
    weight: num(pickFirst(item, ["權重", "weight"])),
    scoring: str(pickFirst(item, ["是否計分", "scoring"])),
  };
}

export function toTopicRelations(raw: RawSnapshot): TopicRelationView[] {
  return (raw.topicRelations ?? [])
    .map((relation) => relationView(relation))
    .filter((relation): relation is TopicRelationView => relation !== null);
}

function stockRelations(stock: RawStock | undefined): TopicRelationView[] {
  const rawRelations = Array.isArray(stock?.topicRelations) ? stock.topicRelations : [];
  return rawRelations
    .map((relation) => relationView(relation))
    .filter((relation): relation is TopicRelationView => relation !== null);
}

function topicNamesFor(stock: RawStock, relations: TopicRelationView[]): string[] {
  const names = new Set<string>();
  for (const relation of relations) names.add(relation.topic);
  for (const value of [stock.topicMain, stock.topicSub]) {
    if (value) {
      for (const part of value.split(/[、,，]/).map((item) => item.trim()).filter(Boolean)) names.add(part);
    }
  }
  return Array.from(names);
}

function volumeRatioOf(stock: RawStock): number | null {
  return num(pickFirst(stock.technical, ["量比", "5日均量倍數", "量能倍數", "成交量比"]));
}

function recordHasValue(record: Record<string, unknown> | undefined): boolean {
  return !!record && Object.entries(record).some(([key, value]) => key !== "資料缺口" && value !== null && value !== undefined && String(value).trim() !== "");
}

function signalSummaryOf(stock: RawStock, watch: WatchRow | null) {
  const chipText = str(pick(stock.chip, "資金確認燈號文字"));
  const operationsText = str(pick(stock.fundamental, "基本面催化燈號文字"));
  const riskText = str(pick(stock.risk, "主要風險")) ?? str(pick(stock.risk, "籌碼風險"));
  return {
    chipActive: watch?.hasFunding === true || chipText !== null,
    chipAvailable: recordHasValue(stock.chip),
    operationsActive: watch?.hasCatalyst === true || operationsText !== null,
    operationsAvailable: recordHasValue(stock.fundamental),
    riskActive: watch?.hasRisk === true || riskText !== null,
    riskAvailable: watch !== null || recordHasValue(stock.risk),
  };
}

function bool(v: unknown): boolean | null {
  if (typeof v === "boolean") return v;
  if (typeof v === "number") return v === 1 ? true : v === 0 ? false : null;
  const value = str(v)?.toLowerCase();
  if (["y", "yes", "true", "1", "是", "符合"].includes(value ?? "")) return true;
  if (["n", "no", "false", "0", "否", "不符合"].includes(value ?? "")) return false;
  return null;
}

function breakout20DayHighOf(technical: Record<string, unknown> | undefined): boolean | null {
  const direct = bool(pickFirst(technical, ["突破20日高", "突破近20日高"]));
  if (direct !== null) return direct;
  const signal = str(pick(technical, "突破訊號"));
  if (!signal) return null;
  return signal.includes("突破") && !signal.includes("未突破");
}

function screenerSignalsOf(stock: RawStock) {
  const technical = stock.technical;
  const chip = stock.chip;
  return {
    close: num(pickFirst(technical, ["收盤", "現價", "close"])) ?? num(pickFirst(stock.price, ["現價", "close"])),
    ma20: num(pick(technical, "MA20")),
    ma60: num(pick(technical, "MA60")),
    ma20SlopePct: num(pick(technical, "MA20斜率%")),
    daysAboveMa20: num(pick(technical, "站上MA20天數")),
    reclaimedMa20: bool(pickFirst(technical, ["剛站回MA20", "站回MA20"])),
    movingAverageAlignment: str(pickFirst(technical, ["均線結構", "均線排列"])),
    structureState: str(pick(technical, "結構狀態")),
    rs5Pct: num(pick(technical, "RS5%")),
    rs20Pct: num(pick(technical, "RS20%")),
    rsState: str(pick(technical, "RS狀態")),
    distanceTo20DayHighPct: num(pickFirst(technical, ["距20日高%", "距高%"])),
    breakout20DayHigh: breakout20DayHighOf(technical),
    macdDif: num(pick(technical, "MACD_DIF")),
    macdSignal: num(pick(technical, "MACD_SIGNAL")),
    macdHist: num(pick(technical, "MACD_HIST")),
    macdHistTurnedPositive: bool(pick(technical, "MACD柱翻正")),
    macdGoldenCross: bool(pick(technical, "MACD黃金交叉")),
    difAboveZero: bool(pick(technical, "DIF站上零軸")),
    kdK: num(pick(technical, "KD_K")),
    kdD: num(pick(technical, "KD_D")),
    kdGoldenCross: bool(pick(technical, "KD黃金交叉")),
    kdLowGoldenCross: bool(pick(technical, "KD低檔黃金交叉")),
    kdMidLowGoldenCross: bool(pick(technical, "KD中低檔黃金交叉")),
    rsi14: num(pick(technical, "RSI14")),
    volumeRatio: volumeRatioOf(stock),
    volumeStatus: str(pick(technical, "量能狀態")),
    upVolumeRatio: num(pick(technical, "上漲量比")),
    breakoutWithVolume: bool(pick(technical, "突破放量")),
    pullbackVolumeShrinkRatio: num(pick(technical, "回檔量縮比")),
    restartConfirmed: bool(pick(technical, "再啟動確認")),
    foreignBuyStreakDays: num(pick(chip, "外資連買日")),
    trustBuyStreakDays: num(pick(chip, "投信連買日")),
    institutionsInSync: bool(pick(chip, "法人同步")),
    foreignFiveDayBuyPct: num(pick(chip, "外資5日買超佔量%")),
    trustFiveDayBuyPct: num(pick(chip, "投信5日買超佔量%")),
    largeHolderWeeklyChangePp: num(pickFirst(chip, ["400張以上週增pp", "大戶週增pp"])),
    largeHolder400Pct: num(pick(chip, "400張以上持股%")),
    largeHolder1000Pct: num(pick(chip, "1000張以上持股%")),
    largeHolder1000WeeklyChangePp: num(pick(chip, "1000張以上週增pp")),
    retailHolderWeeklyChangePp: num(pick(chip, "散戶持股週增pp")),
    technicalAsOf: str(pick(technical, "技術資料日期")),
    institutionalAsOf: str(pick(chip, "資料日期")),
    tdccAsOf: str(pick(chip, "大戶資料日期")),
    chipDataGap: str(pick(chip, "資料缺口")),
  };
}

export function toStockUniverse(raw: RawSnapshot): StockView[] {
  const watchRows = toWatchRows(raw);
  const watchByCode = new Map(watchRows.map((row) => [row.code, row]));
  const relationViews = toTopicRelations(raw);
  const relationsByCode = new Map<string, TopicRelationView[]>();
  for (const relation of relationViews) {
    relationsByCode.set(relation.code, [...(relationsByCode.get(relation.code) ?? []), relation]);
  }

  const stocks = Object.entries(raw.stocks ?? {}).map(([code, stock]): StockView => {
    const relations = relationsByCode.get(code)?.length ? relationsByCode.get(code)! : stockRelations(stock);
    const watch = watchByCode.get(code) ?? null;
    return {
      code,
      name: str(stock.name),
      price: num(pickFirst(stock.price, ["現價", "close"])),
      change: num(pickFirst(stock.price, ["漲跌幅", "changePct"])),
      volume: num(pickFirst(stock.price, ["成交量", "volume"])),
      volumeRatio: volumeRatioOf(stock),
      volumeStatus: str(pick(stock.technical, "量能狀態")),
      dataDate: str(pickFirst(stock.price, ["資料日期", "dataDate"])) ?? str(raw.quoteMeta?.dataDate) ?? str(raw.dataDate),
      updatedAt: str(pickFirst(stock.price, ["更新時間", "updatedAt"])) ?? str(raw.quoteMeta?.updatedAt),
      source: str(pickFirst(stock.price, ["資料來源", "source"])) ?? str(raw.quoteMeta?.source),
      fundamental: {
        revenueYoY: num(pick(stock.fundamental, "月營收YoY")),
        revenueMoM: num(pick(stock.fundamental, "月營收MoM")),
        revenue3mYoY: num(pick(stock.fundamental, "近3月累計營收YoY")),
        revenue3mPreviousYoY: num(pick(stock.fundamental, "近3月累計營收YoY前期")),
        asOf: str(pick(stock.fundamental, "資料年月")),
        source: str(pick(stock.fundamental, "資料來源")),
      },
      riskNote: str(pick(stock.risk, "主要風險")) ?? str(pick(stock.entry, "主要風險")),
      dataFreshness: str(pick(stock.quality, "dataFreshness")) ?? str(pick(stock.risk, "dataFreshness")),
      exceptionMessage: str(pick(stock.quality, "exceptionMessage")),
      technicalSubtype: subTypeOf(stock),
      signalSummary: signalSummaryOf(stock, watch),
      screener: screenerSignalsOf(stock),
      topicMain: str(stock.topicMain),
      topicSub: str(stock.topicSub),
      topicNames: topicNamesFor(stock, relations),
      relations,
      watch,
    };
  });

  return stocks.sort((a, b) => {
    const aRank = a.watch?.rank ?? Number.MAX_SAFE_INTEGER;
    const bRank = b.watch?.rank ?? Number.MAX_SAFE_INTEGER;
    if (aRank !== bRank) return aRank - bRank;
    return a.code.localeCompare(b.code);
  });
}

function topicHistoryEntries(raw: RawSnapshot): RawTopicStrengthHistory[] {
  if (Array.isArray(raw.topicStrengthHistory)) return raw.topicStrengthHistory;
  if (!raw.topicStrengthHistory || typeof raw.topicStrengthHistory !== "object") return [];
  return Object.entries(raw.topicStrengthHistory).map(([topic, value]) => ({
    topic,
    points: Array.isArray(value) ? value : (value as { points?: unknown })?.points as RawTopicStrengthHistory["points"],
  }));
}

export function toTopicStrengthHistory(raw: RawSnapshot): TopicStrengthHistoryView[] {
  return topicHistoryEntries(raw).map((entry) => ({
    topic: str(entry.topic) ?? str(entry.name) ?? "未命名題材",
    points: (entry.points ?? [])
      .map((point) => ({
        date: str(point.date) ?? str(point.tradingDate),
        score: num(point.strengthScore) ?? num(point.score),
        grade: str(point.grade),
        strengthState: str(point.strengthState),
      }))
      .filter((point): point is { date: string; score: number | null; grade: string | null; strengthState: string | null } => Boolean(point.date))
      .sort((a, b) => a.date.localeCompare(b.date)),
  }));
}

function radarMetric(raw?: RawRadarMetric): MarketRadarView["breadth"]["aboveMa60"] {
  return { count: num(raw?.count), denominator: num(raw?.denominator), pct: num(raw?.pct) };
}

function radarRotationItem(raw: RawRadarRotationItem) {
  return {
    name: str(raw.name) ?? "未命名題材",
    score: num(raw.score),
    grade: str(raw.grade),
    strengthState: str(raw.strengthState),
    breadth: {
      advance: num(raw.breadth?.advance),
      decline: num(raw.breadth?.decline),
      flat: num(raw.breadth?.flat),
      unavailable: num(raw.breadth?.unavailable),
      denominator: num(raw.breadth?.denominator),
      pct: num(raw.breadth?.pct),
    },
    coverage: radarMetric(raw.coverage),
    stockCount: num(raw.stockCount),
    historyChange14d: num(raw.historyChange14d),
    historyChangeReason: str(raw.historyChangeReason),
    historyPointCount: num(raw.historyPointCount),
    historyStartDate: str(raw.historyStartDate),
    historyEndDate: str(raw.historyEndDate),
    scoreSource: str(raw.scoreSource),
  };
}

function stringRecord(raw?: Record<string, string | null>) {
  return Object.fromEntries(Object.entries(raw ?? {}).map(([key, value]) => [key, str(value)]));
}

export function toMarketRadar(raw: RawSnapshot): MarketRadarView | null {
  const radar = raw.marketRadar;
  if (!radar) return null;
  const history = radar.topicRotation?.history;
  return {
    asOf: str(radar.asOf),
    dataDate: str(radar.dataDate),
    source: stringRecord(radar.source),
    universe: {
      label: str(radar.universe?.label),
      scope: str(radar.universe?.scope),
      total: num(radar.universe?.total),
      priced: num(radar.universe?.priced),
      technicalEligible: num(radar.universe?.technicalEligible),
      missingPrice: num(radar.universe?.missing?.price),
      missingTechnical: num(radar.universe?.missing?.technical),
    },
    breadth: {
      advance: num(radar.breadth?.advance),
      decline: num(radar.breadth?.decline),
      flat: num(radar.breadth?.flat),
      unavailable: num(radar.breadth?.unavailable),
      aboveMa60: radarMetric(radar.breadth?.aboveMa60),
      rs5Positive: radarMetric(radar.breadth?.rs5Positive),
      rs20Positive: radarMetric(radar.breadth?.rs20Positive),
      macdPositive: radarMetric(radar.breadth?.macdPositive),
    },
    chipBreadth: {
      positive: num(radar.chipBreadth?.positive),
      negative: num(radar.chipBreadth?.negative),
      neutral: num(radar.chipBreadth?.neutral),
      missing: num(radar.chipBreadth?.missing),
      denominator: num(radar.chipBreadth?.denominator),
      institutionalAsOf: str(radar.chipBreadth?.institutionalAsOf),
      tdccAsOf: str(radar.chipBreadth?.tdccAsOf),
    },
    groups: (radar.topicRotation?.groups ?? []).map(radarRotationItem),
    topics: (radar.topicRotation?.topics ?? []).map(radarRotationItem),
    history: {
      source: str(history?.source),
      asOf: str(history?.asOf),
      maxTradingDays: num(history?.maxTradingDays),
      availableTradingDates: (history?.availableTradingDates ?? []).map(str).filter((item): item is string => Boolean(item)),
      availableTradingDayCount: num(history?.availableTradingDayCount),
      formalTopicCount: num(history?.formalTopicCount),
      historyHeaderTopicCount: num(history?.historyHeaderTopicCount),
      formalTopicsWithoutHistory: (history?.formalTopicsWithoutHistory ?? []).map(str).filter((item): item is string => Boolean(item)),
      unmappedHistoryTopics: (history?.unmappedHistoryTopics ?? []).map(str).filter((item): item is string => Boolean(item)),
      excludedNonTradingDates: (history?.excludedNonTradingDates ?? []).map(str).filter((item): item is string => Boolean(item)),
      degradationPolicy: str(history?.degradationPolicy),
    },
    definitions: stringRecord(radar.definitions),
  };
}

function decisionTopic(raw: { topic?: string | null; change14d?: number | null; score?: number | null; grade?: string | null }): MarketDecisionView["topicRotationSummary"]["topWarming"][number] {
  return {
    topic: str(raw.topic) ?? "未命名題材",
    change14d: num(raw.change14d),
    score: num(raw.score),
    grade: str(raw.grade),
  };
}

function decisionEvidence(raw: NonNullable<RawMarketDecision["evidence"]>[number]): MarketDecisionView["evidence"][number] {
  return {
    code: str(raw.code),
    label: str(raw.label),
    signal: str(raw.signal),
    count: num(raw.count),
    denominator: num(raw.denominator),
    pct: num(raw.pct),
    detail: str(raw.detail),
    positive: num(raw.positive),
    negative: num(raw.negative),
    missing: num(raw.missing),
  };
}

export function toMarketDecision(raw: RawSnapshot): MarketDecisionView | null {
  const decision = raw.marketDecision;
  if (!decision) return null;
  return {
    version: str(decision.version),
    asOf: str(decision.asOf),
    dataDate: str(decision.dataDate),
    state: { code: str(decision.state?.code), label: str(decision.state?.label) },
    observationMode: { code: str(decision.observationMode?.code), label: str(decision.observationMode?.label) },
    headline: str(decision.headline),
    confidence: {
      code: str(decision.confidence?.code),
      validSignals: num(decision.confidence?.validSignals),
      totalSignals: num(decision.confidence?.totalSignals),
    },
    evidence: (decision.evidence ?? []).map(decisionEvidence),
    risks: (decision.risks ?? []).map((risk) => ({
      code: str(risk.code),
      label: str(risk.label),
      severity: str(risk.severity),
      detail: str(risk.detail),
    })),
    topicRotationSummary: {
      warmingCount: num(decision.topicRotationSummary?.warmingCount),
      coolingCount: num(decision.topicRotationSummary?.coolingCount),
      flatCount: num(decision.topicRotationSummary?.flatCount),
      missingCount: num(decision.topicRotationSummary?.missingCount),
      topWarming: (decision.topicRotationSummary?.topWarming ?? []).map(decisionTopic),
      topCooling: (decision.topicRotationSummary?.topCooling ?? []).map(decisionTopic),
    },
  };
}
