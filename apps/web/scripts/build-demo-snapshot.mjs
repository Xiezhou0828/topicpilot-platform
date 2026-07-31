import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtureDir = path.resolve(here, "../../../fixtures/demo");
const outputs = [
  path.resolve(here, "../app/lib/web_snapshot.json"),
  path.resolve(here, "../public/data/web_snapshot.json"),
];

async function json(name) {
  return JSON.parse(await readFile(path.join(fixtureDir, name), "utf8"));
}

function byKey(items, key) {
  return new Map(items.map((item) => [item[key], item]));
}

function latestFor(items, date, key, value) {
  return items.find((item) => item.dataDate === date && item[key] === value) ?? null;
}

async function buildSnapshot() {
  const [manifest, stocks, topics, hierarchy, relations, daily, strategies, performance] = await Promise.all([
    json("manifest.json"),
    json("stocks.json"),
    json("topics.json"),
    json("topic_hierarchy.json"),
    json("stock_topic_relations.json"),
    json("daily_snapshots.json"),
    json("strategy_candidates.json"),
    json("strategy_performance.json"),
  ]);

  const dataDate = manifest.dataDate;
  const stockByCode = byKey(stocks, "code");
  const topicBySlug = byKey(topics, "slug");
  const market = daily.marketSnapshots.find((item) => item.dataDate === dataDate) ?? null;
  const normalizedRelations = relations.map((item) => {
    const stock = stockByCode.get(item.stockCode);
    const topic = topicBySlug.get(item.topicSlug);
    return {
      stockCode: item.stockCode,
      stockName: stock?.name ?? null,
      topicSlug: item.topicSlug,
      topicName: topic?.name ?? null,
      groupName: topic?.groupName ?? null,
      relationType: item.relationType,
      weight: item.weight,
      evidenceSummary: item.evidenceSummary,
    };
  });

  const relationsByStock = new Map();
  const constituentsByTopic = new Map();
  for (const relation of normalizedRelations) {
    relationsByStock.set(relation.stockCode, [...(relationsByStock.get(relation.stockCode) ?? []), relation]);
    constituentsByTopic.set(relation.topicSlug, [...(constituentsByTopic.get(relation.topicSlug) ?? []), relation.stockCode]);
  }

  const stockPayload = Object.fromEntries(stocks.map((stock) => {
    const point = latestFor(daily.stockSnapshots, dataDate, "stockCode", stock.code);
    const stockRelations = relationsByStock.get(stock.code) ?? [];
    const primary = stockRelations.find((item) => item.relationType === "PRIMARY") ?? null;
    const secondary = stockRelations.find((item) => item.relationType === "SECONDARY") ?? null;
    return [stock.code, {
      code: stock.code,
      name: stock.name,
      price: {
        close: point?.price ?? null,
        changePct: point?.changePct ?? null,
        volume: point?.volume ?? null,
        dataDate,
      },
      technical: {
        MA5: point?.ma5 ?? null,
        MA20: point?.ma20 ?? null,
        "RS20%": point?.rs20 ?? null,
        state: point?.technicalState ?? null,
      },
      chip: { score: point?.chipScore ?? null },
      risk: { dataFreshness: point?.dataFreshness ?? null },
      topicMain: primary?.topicName ?? null,
      topicSub: secondary?.topicName ?? null,
      topicMainWeight: primary?.weight ?? null,
      topicSubWeight: secondary?.weight ?? null,
      topicRelations: stockRelations,
      quality: point?.metadata ?? { synthetic: true },
    }];
  }));

  const topicPayload = topics.map((topic) => {
    const point = latestFor(daily.topicSnapshots, dataDate, "topicSlug", topic.slug);
    const constituents = [...new Set(constituentsByTopic.get(topic.slug) ?? [])].sort();
    return {
      slug: topic.slug,
      name: topic.name,
      group: topic.groupName,
      type: topic.topicType,
      grade: point?.grade ?? null,
      strengthState: point?.strengthState ?? null,
      score: point?.score ?? null,
      strengthScore: point?.score ?? null,
      stockCount: constituents.length,
      observedCount: point?.advanceCount == null ? null : point.advanceCount + (point.declineCount ?? 0) + (point.unchangedCount ?? 0),
      breadthRatio: point?.coveragePct ?? null,
      leaders: constituents.slice(0, 5),
    };
  });

  const childrenByParent = new Map();
  for (const edge of hierarchy) {
    const parent = topicBySlug.get(edge.parentSlug);
    const child = topicBySlug.get(edge.childSlug);
    if (!parent || !child) continue;
    childrenByParent.set(parent.name, [...(childrenByParent.get(parent.name) ?? []), child.name]);
  }

  const strategyRunByKey = byKey(strategies.strategyRuns, "strategyKey");
  const strategyCandidates = strategies.candidates.map((item) => {
    const stock = stockByCode.get(item.stockCode);
    const primary = (relationsByStock.get(item.stockCode) ?? []).find((relation) => relation.relationType === "PRIMARY") ?? null;
    return {
      strategyId: item.strategyKey,
      strategyKey: [item.dataDate, item.strategyKey, item.stockCode, item.modelVersion].join("|"),
      modelVersion: item.modelVersion,
      batchDate: item.dataDate,
      rank: item.rank,
      code: item.stockCode,
      name: stock?.name ?? null,
      majorGroup: primary?.groupName ?? null,
      fineTopic: primary?.topicName ?? null,
      score: item.score,
      reason: item.reason,
      price: item.price,
      dataDate: item.dataDate,
      dataTime: manifest.generatedAt,
      selected: item.selected,
      trigger: item.triggerPrice,
      support: item.supportPrice,
      invalidation: item.invalidationPrice,
    };
  });

  const strategyPerformance = strategies.strategyRuns.map((run) => {
    const rows = performance.filter((item) => item.strategyKey === run.strategyKey);
    const horizons = Object.fromEntries(rows.map((row) => [row.horizon, {
      status: row.status,
      sampleCount: row.sampleCount,
      winRate: row.winRatePct,
      avgReturnPct: row.averageReturnPct,
      reason: row.reason,
    }]));
    return {
      strategyId: run.strategyKey,
      strategyKey: run.strategyKey,
      name: run.name,
      modelVersion: run.modelVersion,
      dataDate: run.dataDate,
      status: rows.some((row) => row.status === "AVAILABLE") ? "AVAILABLE" : "SAMPLE_ACCUMULATING",
      sampleCount: run.selectedCount,
      availableHorizonCount: rows.filter((row) => row.status === "AVAILABLE").length,
      horizons,
      source: "PostgreSQL synthetic read model",
    };
  });

  const missingPrice = stocks.filter((stock) => stockPayload[stock.code].price.close == null).map((stock) => stock.code).sort();
  return {
    snapshotVersion: "enterprise-db-001",
    classification: manifest.source.classification,
    generatedAt: manifest.generatedAt,
    dataDate,
    compatibilityNotes: [
      "This public portfolio uses only synthetic issuers, prices, scores, and performance values.",
      "Private-only market decisions, observations, positions, and licensed content are omitted.",
    ],
    contracts: {
      enterpriseBundle: { version: manifest.contractVersion },
      strategyRegistry: { version: "enterprise-strategy-registry-001" },
      strategyCandidates: { version: "enterprise-strategy-candidates-001" },
      strategyPerformance: { version: "enterprise-strategy-performance-001" },
    },
    quoteMeta: {
      status: market?.status ?? "NOT_RUN",
      dataDate,
      updatedAt: manifest.generatedAt,
      source: manifest.source.name,
      totalSymbols: stocks.length,
      successSymbols: stocks.length - missingPrice.length,
      failedSymbols: missingPrice.length,
      failedCodes: missingPrice,
    },
    marketSession: {
      market: market?.market ?? null,
      timezone: "Asia/Taipei",
      currentDate: dataDate,
      latestTradingDate: dataDate,
      isTradingDay: true,
      session: "CLOSED",
      reason: "Historical enterprise read model",
      nextTradingDate: null,
    },
    quality: {
      priceRows: stocks.length - missingPrice.length,
      technicalRows: stocks.filter((stock) => stockPayload[stock.code].technical.state != null).length,
      chipRows: stocks.filter((stock) => stockPayload[stock.code].chip.score != null).length,
      fundamentalRows: 0,
      entryRows: 0,
      dailyObservationRows: 0,
      dailyObservationSource: null,
      entrySource: null,
      universe: stocks.length,
      missingPrice,
      missingTechnical: stocks.filter((stock) => stockPayload[stock.code].technical.state == null).map((stock) => stock.code).sort(),
      missingChip: stocks.filter((stock) => stockPayload[stock.code].chip.score == null).map((stock) => stock.code).sort(),
      missingFundamental: stocks.map((stock) => stock.code).sort(),
      missingEntry: stocks.map((stock) => stock.code).sort(),
      unavailableTechnicalFields: [],
    },
    market: { indices: [] },
    topics: topicPayload,
    topicGroups: [...childrenByParent.entries()].map(([name, children]) => ({ name, children, childCount: children.length })),
    topicRelations: normalizedRelations,
    topicStrengthHistory: topics.map((topic) => ({
      slug: topic.slug,
      topic: topic.name,
      points: daily.topicSnapshots
        .filter((point) => point.topicSlug === topic.slug)
        .map((point) => ({ date: point.dataDate, score: point.score, grade: point.grade, strengthState: point.strengthState })),
    })),
    strategyRegistry: {
      version: "enterprise-strategy-registry-001",
      dataDate,
      strategies: [...strategyRunByKey.values()].map((run) => ({
        strategyId: run.strategyKey,
        name: run.name,
        modelVersion: run.modelVersion,
        batchDate: run.dataDate,
        batchStatus: run.status,
        candidateCount: run.candidateCount,
        selectedCount: run.selectedCount,
        rankingCount: run.candidateCount,
        missingReason: null,
      })),
    },
    strategyCandidates,
    strategyPerformance,
    dailyObservation: [],
    entrySetups: [],
    stocks: stockPayload,
  };
}

const content = `${JSON.stringify(await buildSnapshot(), null, 2)}\n`;
if (process.argv.includes("--check")) {
  const mismatches = [];
  for (const output of outputs) {
    try {
      if (await readFile(output, "utf8") !== content) mismatches.push(output);
    } catch {
      mismatches.push(output);
    }
  }
  if (mismatches.length) {
    console.error(`Demo snapshot is out of date:\n${mismatches.join("\n")}`);
    process.exit(1);
  }
  console.log("Demo snapshot matches fixtures/demo.");
} else {
  await Promise.all(outputs.map((output) => writeFile(output, content, "utf8")));
  console.log(`Generated ${outputs.length} synthetic demo snapshots.`);
}
