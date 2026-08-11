export const FAVORITES_STORAGE_KEY = "topic-pilot-favorites";
export const TOPIC_FAVORITES_STORAGE_KEY = "topic-pilot-topic-favorites";
export const FAVORITES_CHANGED_EVENT = "topic-pilot-favorites-changed";

export function normalizeFavoriteCodes(value) {
  if (!Array.isArray(value)) return [];
  const seen = new Set();
  const codes = [];
  for (const item of value) {
    const code = String(item ?? "").trim();
    if (!code || seen.has(code)) continue;
    seen.add(code);
    codes.push(code);
  }
  return codes;
}

function mainGroupOf(stock) {
  const relation = (stock?.relations ?? []).find((item) => item.parentGroup?.trim());
  return relation?.parentGroup?.trim() || "待分類";
}

function fineTopicsOf(stock) {
  const topics = [];
  for (const relation of stock?.relations ?? []) {
    if (relation.topic?.trim() && !topics.includes(relation.topic.trim())) topics.push(relation.topic.trim());
  }
  for (const topic of stock?.topicNames ?? []) {
    if (topic?.trim() && !topics.includes(topic.trim())) topics.push(topic.trim());
  }
  return topics.length ? topics : ["待分類"];
}

export function buildFavoriteEntries(codes, stocks, snapshotAvailable = true) {
  const byCode = new Map((stocks ?? []).map((stock) => [stock.code, stock]));
  return normalizeFavoriteCodes(codes).map((code, order) => {
    const stock = byCode.get(code) ?? null;
    return {
      code,
      order,
      stock,
      mainGroup: stock ? mainGroupOf(stock) : "待分類",
      fineTopics: stock ? fineTopicsOf(stock) : ["待分類"],
      status: !snapshotAvailable ? "snapshot-unavailable" : stock ? "available" : "missing-stock",
    };
  });
}

export function filterFavoriteEntries(entries, query) {
  const keyword = String(query ?? "").trim().toLowerCase();
  if (!keyword) return entries;
  return entries.filter((entry) => [
    entry.code,
    entry.stock?.name,
    entry.mainGroup,
    ...(entry.fineTopics ?? []),
  ].filter(Boolean).join(" ").toLowerCase().includes(keyword));
}

export function groupFavoriteEntries(entries) {
  const groups = new Map();
  for (const entry of entries) {
    const groupName = entry.mainGroup || "待分類";
    if (!groups.has(groupName)) groups.set(groupName, new Map());
    const topics = groups.get(groupName);
    const topic = entry.fineTopics?.[0] || "待分類";
    if (!topics.has(topic)) topics.set(topic, []);
    topics.get(topic).push(entry);
  }
  return Array.from(groups, ([name, topics]) => ({
    name,
    topics: Array.from(topics, ([name, items]) => ({ name, items })),
  }));
}
