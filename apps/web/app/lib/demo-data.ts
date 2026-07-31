import type {
  DataStatus,
  StockDetail,
  StockSummary,
  StrategyCandidate,
  StrategyPerformance,
  StrategySummary,
  TopicDetail,
  TopicRotationItem,
  TopicSummary,
} from "./types";

export const DEMO_DATA_DATE = "2026-07-31";

export const demoStatus: DataStatus = {
  dataDate: DEMO_DATA_DATE,
  updatedAt: "2026-07-31T07:02:31Z",
  bundleVersion: "enterprise_bundle.v1",
  sourceMode: "synthetic_demo",
  apiStatus: "healthy",
  databaseStatus: "healthy",
  latencyMs: 84,
  counts: { stocks: 6, topics: 5, strategyCandidates: 12 },
  quality: { passed: 28, warnings: 1, failed: 0 },
};

export const demoStocks: StockSummary[] = [
  { code: "SYN-101", name: "星河運算", market: "DEMO", group: "數位基礎建設", price: 128.5, changePct: 2.36, volumeRatio: 1.82, signal: "相對強勢", topicNames: ["邊緣運算", "液冷模組"], updatedAt: "2026-07-31T06:55:00Z" },
  { code: "SYN-204", name: "嶼光模組", market: "DEMO", group: "先進顯示", price: 74.2, changePct: 1.09, volumeRatio: 1.21, signal: "結構改善", topicNames: ["新世代顯示", "車載光學"], updatedAt: "2026-07-31T06:54:00Z" },
  { code: "SYN-318", name: "森流能源", market: "DEMO", group: "能源轉型", price: null, changePct: null, volumeRatio: 0.94, signal: "資料待補", topicNames: ["儲能調度"], updatedAt: "2026-07-31T06:52:00Z" },
  { code: "SYN-427", name: "稜鏡網通", market: "DEMO", group: "通訊設備", price: 56.8, changePct: -0.7, volumeRatio: 0.76, signal: "區間整理", topicNames: ["低軌通訊", "邊緣運算"], updatedAt: "2026-07-31T06:50:00Z" },
  { code: "SYN-553", name: "遠岬自動化", market: "DEMO", group: "智慧製造", price: 93.1, changePct: 3.1, volumeRatio: 2.14, signal: "動能升溫", topicNames: ["協作機器人"], updatedAt: "2026-07-31T06:48:00Z" },
  { code: "SYN-689", name: "藍潮材料", market: "DEMO", group: "先進材料", price: 41.6, changePct: -1.18, volumeRatio: null, signal: "等待確認", topicNames: ["低碳材料", "儲能調度"], updatedAt: null },
];

export const demoStockDetails: StockDetail[] = demoStocks.map((stock, index) => ({
  ...stock,
  description: [
    "模擬的高效運算設備供應商，用於展示題材關聯、技術指標與資料品質欄位。",
    "模擬的光學模組製造商，展示跨題材關聯與基本面摘要。",
    "模擬的能源調度服務商；部分欄位刻意保留空值以驗證 null handling。",
    "模擬的通訊設備供應商，用於呈現區間整理狀態。",
    "模擬的工業自動化整合商，用於呈現策略候選與題材升溫訊號。",
    "模擬的新材料開發商；資料更新時間刻意缺漏以展示品質提示。",
  ][index],
  technical: {
    trend: ["多週期偏強", "中期翻揚", "待補資料", "橫向整理", "動能擴張", "弱勢反彈"][index],
    aboveMa20: index === 2 ? null : [true, true, null, false, true, false][index],
    relativeStrength20: [78.4, 65.2, null, 44.8, 82.1, 38.7][index],
    volatility20: [2.4, 1.8, null, 1.2, 3.1, 2.7][index],
  },
  fundamental: {
    revenueYoy: [18.6, 9.4, null, -2.1, 24.7, 3.8][index],
    revenueMom: [4.2, 1.8, null, 0.6, 6.1, -1.4][index],
    grossMargin: [31.4, 22.8, null, 18.2, 28.6, 16.9][index],
  },
  qualityNotes: index === 2
    ? ["收盤價尚未通過來源驗證，因此保留為 null。", "此筆資料僅用於空值介面驗證。"]
    : index === 5
      ? ["成交量比與更新時間缺漏，未以 0 取代。"]
      : ["合成資料已通過格式與關聯完整性檢查。"],
}));

const topicBase: TopicSummary[] = [
  { slug: "edge-computing", name: "邊緣運算", parentName: "數位基礎建設", grade: "S", score: 8.7, change14d: 2.4, memberCount: 2, state: "升溫" },
  { slug: "robotics", name: "協作機器人", parentName: "智慧製造", grade: "A", score: 7.1, change14d: 1.5, memberCount: 1, state: "升溫" },
  { slug: "next-display", name: "新世代顯示", parentName: "先進顯示", grade: "A", score: 6.4, change14d: 0.6, memberCount: 1, state: "穩定" },
  { slug: "energy-storage", name: "儲能調度", parentName: "能源轉型", grade: "B", score: 4.3, change14d: -0.8, memberCount: 2, state: "盤整" },
  { slug: "leo-network", name: "低軌通訊", parentName: "通訊設備", grade: "B", score: null, change14d: null, memberCount: 1, state: "資料待補" },
];

export const demoTopics = topicBase;

const trendDates = ["07-18", "07-21", "07-22", "07-23", "07-24", "07-25", "07-28", "07-29", "07-30", "07-31"];

export const demoTopicDetails: TopicDetail[] = topicBase.map((topic, topicIndex) => ({
  ...topic,
  description: `${topic.name}為匿名化題材，用於展示階層關聯、14 日強度與成分標的查詢，不代表真實市場分類。`,
  trend: trendDates.map((date, index) => ({
    date: `2026-${date}`,
    score: topic.score === null ? null : Number((topic.score - (9 - index) * (topic.change14d ?? 0) / 12 + Math.sin(index + topicIndex) * 0.22).toFixed(2)),
  })),
  stocks: demoStocks.filter((stock) => stock.topicNames.includes(topic.name)),
}));

export const demoRotation: TopicRotationItem[] = topicBase.map((topic) => ({
  ...topic,
  direction: topic.change14d === null ? "steady" : topic.change14d > 0.7 ? "warming" : topic.change14d < -0.4 ? "cooling" : "steady",
}));

export const demoStrategies: StrategySummary[] = [
  { key: "MAS", name: "均線結構", summary: "觀察多週期均線排列與價格位置，篩出結構持續改善的標的。", status: "COMPLETE", candidateCount: 2, dataDate: DEMO_DATA_DATE },
  { key: "MAV", name: "量價動能", summary: "交叉檢視成交量擴張、價格動能與相對強弱。", status: "COMPLETE", candidateCount: 2, dataDate: DEMO_DATA_DATE },
  { key: "TMC", name: "題材籌碼", summary: "結合題材升溫速度與籌碼一致性，觀察族群內部擴散。", status: "COMPLETE", candidateCount: 2, dataDate: DEMO_DATA_DATE },
  { key: "BB", name: "波動突破", summary: "以波動收斂與區間突破辨識可能的狀態轉換。", status: "COMPLETE", candidateCount: 2, dataDate: DEMO_DATA_DATE },
  { key: "PB", name: "趨勢回檔", summary: "在中期結構未破壞時，追蹤回檔後的強弱修復。", status: "COMPLETE", candidateCount: 2, dataDate: DEMO_DATA_DATE },
  { key: "KD", name: "動能轉折", summary: "以動能指標與價格確認條件辨識短週期轉折。", status: "COMPLETE", candidateCount: 2, dataDate: DEMO_DATA_DATE },
];

export const demoCandidates: StrategyCandidate[] = demoStrategies.flatMap((strategy, strategyIndex) => {
  const first = demoStocks[strategyIndex % demoStocks.length];
  const second = demoStocks[(strategyIndex + 2) % demoStocks.length];
  return [first, second].map((stock, index) => ({
    strategyKey: strategy.key,
    rank: index + 1,
    code: stock.code,
    name: stock.name,
    score: Number((88.4 - strategyIndex * 2.7 - index * 6.1).toFixed(1)),
    price: stock.price,
    topic: stock.topicNames[0] ?? null,
    reason: index === 0 ? "主要條件一致，資料完整度通過門檻。" : "次要候選，仍需等待下一批資料確認。",
    dataDate: DEMO_DATA_DATE,
  }));
});

export const demoPerformance: StrategyPerformance[] = demoStrategies.flatMap((strategy, index) => [
  { strategyKey: strategy.key, horizon: "5D", sampleCount: 24 + index * 3, returnPct: Number((1.9 - index * 0.22).toFixed(2)), winRatePct: Number((61.8 - index * 2.1).toFixed(1)) },
  { strategyKey: strategy.key, horizon: "10D", sampleCount: 18 + index * 2, returnPct: Number((3.1 - index * 0.31).toFixed(2)), winRatePct: Number((64.2 - index * 1.8).toFixed(1)) },
]);
