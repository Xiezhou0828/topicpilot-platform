export type MarketIndex = {
  name: string;
  value: string;
  change: number;
  stance: "risk-on" | "neutral" | "risk-off";
};

export type Topic = {
  name: string;
  group: string;
  grade: "S" | "A" | "B" | "D";
  score: number;
  heat: number;
  breadth: string;
  signal: "消息共振" | "資金先行" | "消息背離" | "暫不關注";
  leaders: string[];
  action: string;
  note: string;
};

export type NewsItem = {
  time: string;
  topic: string;
  title: string;
  source: string;
  impact: "共振" | "先行" | "雜訊" | "背離";
  heat: number;
};

export type WatchItem = {
  rank: number;
  code: string;
  name: string;
  topic: string;
  setup: string;
  status: "等突破" | "等回測" | "暫不試單";
  price: number;
  trigger?: number;
  stop: number;
  distance?: number;
  risk?: number;
  gate: "PASS" | "WARN" | "BLOCK";
  foreignFlow: number;
  marginChange: number;
  bigBuyer: boolean;
  strongThisWeek: boolean;
};

export type AiTrader = {
  name: string;
  model: string;
  style: string;
  persona: string;
  riskProfile: "積極" | "平衡" | "保守";
  mood: string;
  capitalMode: string;
  returnRate: number;
  winRate: number;
  maxDrawdown: number;
  idea: string;
  picks: string[];
  holdings: { code: string; name: string; weight: number; note: string }[];
  bullish: string[];
  bearish: string[];
  quote: string;
  blindSpot: string;
  equity: number[];
};

export type StudioMessage = { speaker: string; tone: string; text: string; topic: string };

// 這些值只在 Snapshot 契約失效時作為 UI 安全退路；所有名稱與數值皆為合成資料。
export const marketIndices: MarketIndex[] = [
  { name: "Demo Market", value: "1,024.8", change: 0.62, stance: "neutral" },
];

export const topics: Topic[] = [
  {
    name: "Edge AI",
    group: "Digital Infrastructure",
    grade: "A",
    score: 4.6,
    heat: 72,
    breadth: "1 / 2",
    signal: "資金先行",
    leaders: ["Aster Systems"],
    action: "公開資料展示",
    note: "完全合成的題材資料，用於展示 TopicPilot 原版前端。",
  },
  {
    name: "Cloud Security",
    group: "Digital Infrastructure",
    grade: "A",
    score: 4.4,
    heat: 68,
    breadth: "1 / 1",
    signal: "消息共振",
    leaders: ["Cipher Cloud"],
    action: "公開資料展示",
    note: "完全合成的題材資料，不代表任何真實公司或投資建議。",
  },
];

export const news: NewsItem[] = [
  { time: "08:00", topic: "Edge AI", title: "Synthetic portfolio event for interface demonstration", source: "Demo fixture", impact: "先行", heat: 72 },
];

export const watchlist: WatchItem[] = [
  { rank: 1, code: "DEMO-A1", name: "Aster Systems", topic: "Edge AI", setup: "Synthetic trend example", status: "等突破", price: 45.2, trigger: 45.5, stop: 42.9, distance: 0.66, risk: 5.09, gate: "PASS", foreignFlow: 0, marginChange: 0, bigBuyer: false, strongThisWeek: true },
];

export const aiTraders: AiTrader[] = [];
export const studioMessages: StudioMessage[] = [];
