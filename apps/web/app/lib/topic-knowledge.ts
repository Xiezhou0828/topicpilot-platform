export type TopicKnowledge = {
  topicId: string;
  displayName: string;
  parentId: string | null;
  aliases: string[];
  englishName?: string;
  summary: string;
  industryPath: string[];
  applications?: string[];
  industryWatchPoints?: string[];
  scope?: { focus?: string; distinction?: string };
  contentVersion: string;
};

// Durable, human-curated definitions only. This file never owns membership,
// role, Strength, Grade, Lifecycle, or recommendation authority.
const KNOWLEDGE: Record<string, TopicKnowledge> = {
  "ai-server": {
    topicId: "ai-server",
    displayName: "AI伺服器",
    parentId: "電子",
    aliases: ["AI server", "AI伺服器供應鏈"],
    englishName: "AI server",
    summary: "提供 AI 訓練與推論所需的伺服器、機櫃與相關系統整合能力。",
    industryPath: ["電子", "伺服器與資料中心", "AI伺服器"],
    applications: ["雲端資料中心", "企業 AI", "高效能運算"],
    industryWatchPoints: ["系統整合與散熱需求", "資料中心資本支出", "供應鏈分工"],
    scope: { focus: "AI 運算基礎設施與伺服器供應鏈。", distinction: "不等同於所有 AI 軟體或一般伺服器題材。" },
    contentVersion: "topic-knowledge.v1",
  },
  "optical-communication": {
    topicId: "optical-communication",
    displayName: "光通訊",
    parentId: "電子",
    aliases: ["optical communications", "光通訊元件"],
    englishName: "Optical communications",
    summary: "涵蓋以光訊號傳輸資料所需的元件、模組與相關連接技術。",
    industryPath: ["電子", "通訊與網路", "光通訊"],
    applications: ["資料中心互連", "電信網路", "高速網路"],
    industryWatchPoints: ["傳輸速率升級", "資料中心網路建置", "元件與模組供應鏈"],
    scope: { focus: "光訊號傳輸與網路互連。", distinction: "不以單一公司或單一產品線代表整個產業。" },
    contentVersion: "topic-knowledge.v1",
  },
};

export function getTopicKnowledge(topic: { slug: string; name: string; groupName?: string | null }): TopicKnowledge | null {
  return KNOWLEDGE[topic.slug] ?? null;
}

export function knowledgeSearchText(knowledge: TopicKnowledge | null): string {
  if (!knowledge) return "";
  return [knowledge.displayName, knowledge.englishName, ...knowledge.aliases, knowledge.summary].filter(Boolean).join(" ");
}
