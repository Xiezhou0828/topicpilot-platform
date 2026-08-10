export type PreviewLifecycleSegment = {
  stage: "萌芽" | "發酵" | "主升" | "高檔整理" | "退潮";
  entered: string;
  duration: string;
  active?: boolean;
};

export type PreviewTopicEvent = {
  date: string;
  title: string;
  detail: string;
};

export type PreviewTopicNews = {
  time: string;
  title: string;
  source: string;
};

export type PreviewRelatedTopic = {
  slug: string;
  name: string;
  strength: number;
  grade: "S" | "A" | "B" | "D";
  state: string;
};

export type PreviewHeatmapCell = PreviewRelatedTopic & {
  span: number;
  rows: number;
};

export type TopicPreview = {
  summary: string;
  lifecycle: {
    current: PreviewLifecycleSegment["stage"];
    entered: string;
    duration: string;
    segments: PreviewLifecycleSegment[];
  };
  events: PreviewTopicEvent[];
  news: PreviewTopicNews[];
  related: PreviewRelatedTopic[];
  heatmap: PreviewHeatmapCell[];
  metrics: {
    participation: string;
    leaderDrive: string;
    leaderConsistency: string;
    completeness: string;
    scoring: string;
  };
};

export type PreviewTopicIdentity = {
  name: string;
  groupName: string | null;
  score: number;
  grade: "S" | "A" | "B" | "D";
  state: string;
  constituents: Array<{ code: string; name: string; relationType: string; weight: number | null; price: number | null; changePct: number | null }>;
};

const previewIdentities: Record<string, PreviewTopicIdentity> = {
  "ai-server": {
    name: "AI伺服器", groupName: "電子", score: 92, grade: "S", state: "全面走強",
    constituents: [
      { code: "2382", name: "廣達", relationType: "PRIMARY", weight: 1, price: 312.5, changePct: 3.2 },
      { code: "2317", name: "鴻海", relationType: "PRIMARY", weight: 0.9, price: 198, changePct: 1.54 },
      { code: "6669", name: "緯穎", relationType: "CORE", weight: 0.8, price: 2385, changePct: 2.8 },
      { code: "3231", name: "緯創", relationType: "CORE", weight: 0.7, price: 128.5, changePct: 2.39 },
      { code: "3017", name: "奇鋐", relationType: "RELATED", weight: 0.5, price: 742, changePct: 1.78 },
    ],
  },
  bbu: {
    name: "BBU", groupName: "能源與儲能", score: 66, grade: "S", state: "高檔分歧",
    constituents: [
      { code: "2308", name: "台達電", relationType: "PRIMARY", weight: 1, price: 410, changePct: 1.2 },
      { code: "3015", name: "全漢", relationType: "CORE", weight: 0.8, price: 108, changePct: -0.4 },
    ],
  },
  cpo: {
    name: "CPO", groupName: "電子", score: 78, grade: "A", state: "升溫中", constituents: [
      { code: "3081", name: "聯亞", relationType: "PRIMARY", weight: 1, price: 512, changePct: 2.1 },
      { code: "3163", name: "波若威", relationType: "CORE", weight: 0.7, price: 168, changePct: 1.4 },
    ],
  },
  asic: {
    name: "ASIC", groupName: "電子", score: 74, grade: "A", state: "開始轉強", constituents: [
      { code: "3661", name: "世芯-KY", relationType: "PRIMARY", weight: 1, price: 2820, changePct: 1.1 },
      { code: "3443", name: "創意", relationType: "CORE", weight: 0.7, price: 1190, changePct: 0.8 },
    ],
  },
  pcb: {
    name: "PCB", groupName: "電子", score: 58, grade: "B", state: "量能回流", constituents: [
      { code: "2313", name: "華通", relationType: "PRIMARY", weight: 1, price: 82.4, changePct: -0.6 },
      { code: "8046", name: "南電", relationType: "CORE", weight: 0.7, price: 154, changePct: 0.3 },
    ],
  },
};

export function getPreviewTopicIdentity(slug: string): PreviewTopicIdentity | null {
  return previewIdentities[slug] ?? null;
}

export function getPreviewTopicIdentities(): Array<[string, PreviewTopicIdentity]> {
  return Object.entries(previewIdentities);
}

const stages: PreviewLifecycleSegment[] = [
  { stage: "萌芽", entered: "7/22 進入", duration: "2 個交易日" },
  { stage: "發酵", entered: "7/24 進入", duration: "3 個交易日" },
  { stage: "主升", entered: "7/28 進入", duration: "已持續 4 個交易日", active: true },
  { stage: "高檔整理", entered: "尚未進入", duration: "—" },
  { stage: "退潮", entered: "尚未進入", duration: "—" },
];

const previewBySlug: Record<string, Partial<TopicPreview>> = {
  "ai-server": {
    summary: "AI 伺服器仍是目前市場主線，代表股與核心成員維持同步強勢，資金開始向高速傳輸與散熱鏈擴散。",
    events: [
      { date: "7/22", title: "開始升溫", detail: "伺服器供應鏈出現第一批同步轉強個股。" },
      { date: "7/24", title: "升至 A", detail: "代表股量價同步，核心成員開始擴散。" },
      { date: "7/28", title: "升至 S", detail: "市場主線確立，題材強度與參與度同步上升。" },
      { date: "今天", title: "維持主線", detail: "盤中仍有資金集中，暫未出現主線退出訊號。" },
    ],
    news: [
      { time: "10:32", title: "AI 伺服器需求持續增加", source: "Preview 新聞" },
      { time: "09:48", title: "BBU 開始高檔震盪", source: "Preview 新聞" },
      { time: "09:18", title: "ASIC 同步轉強", source: "Preview 新聞" },
    ],
    related: [
      { slug: "cpo", name: "CPO", strength: 78, grade: "A", state: "升溫中" },
      { slug: "asic", name: "ASIC", strength: 74, grade: "A", state: "開始轉強" },
      { slug: "bbu", name: "BBU", strength: 66, grade: "S", state: "高檔分歧" },
    ],
  },
  bbu: {
    summary: "BBU 維持高檔整理，題材強度仍高，但族群內部開始出現分歧，後續需觀察核心成員是否重新同步。",
    lifecycle: { current: "高檔整理", entered: "8/2 進入", duration: "已持續 3 個交易日", segments: stages.map((item) => item.stage === "主升" ? { ...item, active: false } : item.stage === "高檔整理" ? { ...item, active: true } : item) },
    events: [
      { date: "7/24", title: "升至 A", detail: "代表股先行，核心成員陸續加入。" },
      { date: "7/29", title: "升至 S", detail: "題材強度升高，市場關注度集中。" },
      { date: "今天", title: "高檔分歧", detail: "代表股仍強，但關聯股表現不一。" },
    ],
    news: [
      { time: "10:08", title: "BBU 開始高檔震盪", source: "Preview 新聞" },
      { time: "昨日", title: "儲能需求維持市場關注", source: "Preview 新聞" },
    ],
    related: [
      { slug: "ai-server", name: "AI伺服器", strength: 92, grade: "S", state: "全面走強" },
      { slug: "asic", name: "ASIC", strength: 74, grade: "A", state: "升溫中" },
      { slug: "pcb", name: "PCB", strength: 58, grade: "B", state: "量能回流" },
    ],
  },
};

const defaultRelated: PreviewRelatedTopic[] = [
  { slug: "cpo", name: "CPO", strength: 78, grade: "A", state: "升溫中" },
  { slug: "asic", name: "ASIC", strength: 74, grade: "A", state: "開始轉強" },
  { slug: "pcb", name: "PCB", strength: 58, grade: "B", state: "量能回流" },
  { slug: "cooling", name: "散熱", strength: 52, grade: "B", state: "觀察中" },
];

function gradeForStrength(strength: number): "S" | "A" | "B" | "D" {
  return strength >= 85 ? "S" : strength >= 70 ? "A" : strength >= 50 ? "B" : "D";
}

function previewHeatmap(topicName: string, strength: number, grade: "S" | "A" | "B" | "D", related: PreviewRelatedTopic[]): PreviewHeatmapCell[] {
  const cells = [{ slug: "current", name: topicName, strength, grade, state: "目前題材" }, ...related];
  return cells.slice(0, 6).map((cell, index) => ({
    ...cell,
    span: index === 0 ? 7 : index < 3 ? 5 : 4,
    rows: index === 0 ? 2 : index < 3 ? 1 : 1,
  }));
}

export function getTopicPreview(slug: string, topicName: string, strength: number | null, grade: string | null): TopicPreview {
  const currentStrength = strength ?? 72;
  const currentGrade = grade === "S" || grade === "A" || grade === "B" || grade === "D" ? grade : gradeForStrength(currentStrength);
  const base = previewBySlug[slug] ?? {};
  const related = base.related ?? defaultRelated;
  return {
    summary: base.summary ?? `${topicName} 目前維持市場關注，Preview 以題材強度、生命階段與相鄰題材呈現完整研究閱讀流程。`,
    lifecycle: base.lifecycle ?? { current: "主升", entered: "7/28 進入", duration: "已持續 4 個交易日", segments: stages },
    events: base.events ?? [
      { date: "7/22", title: "開始升溫", detail: "題材出現第一批同步轉強個股。" },
      { date: "7/28", title: `升至 ${currentGrade}`, detail: "題材強度與市場關注度同步上升。" },
      { date: "今天", title: "維持主線", detail: "目前仍可作為研究入口，等待正式事件 read model。" },
    ],
    news: base.news ?? [
      { time: "10:18", title: `${topicName} 相關供應鏈同步轉強`, source: "Preview 新聞" },
      { time: "09:42", title: "資金開始向相鄰題材擴散", source: "Preview 新聞" },
      { time: "昨日", title: "市場維持對題材的研究關注", source: "Preview 新聞" },
    ],
    related,
    heatmap: previewHeatmap(topicName, currentStrength, currentGrade, related),
    metrics: base.metrics ?? {
      participation: "擴散中",
      leaderDrive: "代表股帶動",
      leaderConsistency: "同步",
      completeness: "Preview",
      scoring: "正式強度",
    },
  };
}

const TOPIC_NAME_LABELS: Record<string, string> = {
  "ai-server": "AI伺服器",
  "digital-infrastructure": "數位基礎建設",
  "edge-ai": "邊緣 AI",
  "cloud-security": "雲端資安",
  "clean-energy": "潔淨能源",
  "high-speed-transmission": "高速傳輸",
  "cooling": "散熱",
  "robotics": "機器人",
};

const GROUP_NAME_LABELS: Record<string, string> = {
  "Digital Infrastructure": "數位基礎建設",
  "Sustainable Systems": "永續系統",
};

export function topicNameLabel(slug: string, name: string): string {
  const mapped = TOPIC_NAME_LABELS[slug] ?? ({ "AI Server": "AI伺服器", "Cloud Security": "雲端資安", "Edge AI": "邊緣 AI", "Clean Energy": "潔淨能源" }[name]);
  if (mapped) return mapped;
  return /[\u4e00-\u9fff]/.test(name) || /^[A-Z0-9\-]+$/.test(name) ? name : "待中文化題材";
}

export function groupNameLabel(name: string | null): string | null {
  return name ? GROUP_NAME_LABELS[name] ?? (/[\u4e00-\u9fff]/.test(name) ? name : "其他題材") : null;
}

export function readableTopicState(value: string | null | undefined): string {
  if (!value) return "資料待更新";
  const labels: Record<string, string> = {
    BROAD_STRENGTH: "全面走強", BROAD: "全面走強", LEADER_FIRST: "龍頭先行",
    WARMING: "急升溫", HEATING: "升溫中", COOLING: "退潮", DIVERGENCE: "高檔分歧",
    WEAKENING: "動能轉弱", MAINLINE: "主線", ACTIVE: "持續強勢", STABLE: "盤整中",
  };
  const normalized = value.trim().toUpperCase();
  return labels[normalized] ?? "狀態待更新";
}

export function readableFreshness(value: string | null): string {
  if (!value) return "資料待更新";
  const labels: Record<string, string> = { CURRENT: "盤中更新", PARTIAL: "部分更新", STALE: "資料稍舊", AFTER_CLOSE: "盤後更新" };
  return labels[value.trim().toUpperCase()] ?? "資料待更新";
}
