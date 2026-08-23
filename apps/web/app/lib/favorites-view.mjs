export const FAVORITES_STORAGE_KEY = "topic-pilot-favorites";
export const TOPIC_FAVORITES_STORAGE_KEY = "topic-pilot-topic-favorites";
export const FAVORITES_CHANGED_EVENT = "topic-pilot-favorites-changed";
export const FAVORITES_SCHEMA_VERSION = 1;
export const FAVORITE_ENTITY_TYPES = Object.freeze({ STOCK: "STOCK", TOPIC: "TOPIC" });

const ENTITY_TYPES = new Set(Object.values(FAVORITE_ENTITY_TYPES));

function normalizeEntityType(value, fallback = FAVORITE_ENTITY_TYPES.STOCK) {
  const entityType = String(value ?? "").trim().toUpperCase();
  if (!entityType) return fallback;
  return ENTITY_TYPES.has(entityType) ? entityType : null;
}

export function stableStockId(code, market = null) {
  const normalizedCode = String(code ?? "").trim();
  const normalizedMarket = String(market ?? "").trim().toUpperCase();
  return normalizedMarket && normalizedCode ? `${normalizedMarket}:${normalizedCode}` : normalizedCode;
}

export function stockCodeFromStableId(stableId) {
  const value = String(stableId ?? "").trim();
  const separator = value.indexOf(":");
  return separator >= 0 ? value.slice(separator + 1) : value;
}

export function stockMarketFromStableId(stableId) {
  const value = String(stableId ?? "").trim();
  const separator = value.indexOf(":");
  return separator > 0 ? value.slice(0, separator).toUpperCase() : null;
}

export function createFavoriteIdentity({ entityType, stableId, displayLabel, market } = {}) {
  const normalizedEntityType = normalizeEntityType(entityType);
  if (!normalizedEntityType) return null;
  const normalizedStableId = normalizedEntityType === FAVORITE_ENTITY_TYPES.STOCK
    ? stableStockId(stableId, market)
    : String(stableId ?? "").trim();
  if (!normalizedStableId) return null;
  const identity = {
    version: FAVORITES_SCHEMA_VERSION,
    entityType: normalizedEntityType,
    stableId: normalizedStableId,
  };
  const label = String(displayLabel ?? "").trim();
  if (label) identity.displayLabel = label;
  return identity;
}

/** @param {unknown} value @param {"STOCK"|"TOPIC"} [entityType] */
export function normalizeFavoriteIdentities(value, entityType = FAVORITE_ENTITY_TYPES.STOCK) {
  const normalizedEntityType = normalizeEntityType(entityType);
  const items = Array.isArray(value) ? value : value && Array.isArray(value.items) ? value.items : [];
  const seen = new Set();
  const identities = [];
  for (const item of items) {
    const identity = typeof item === "string"
      ? createFavoriteIdentity({ entityType: normalizedEntityType, stableId: item })
      : createFavoriteIdentity({ ...item, entityType: item?.entityType ?? normalizedEntityType });
    if (!identity) continue;
    const key = favoriteIdentityKey(identity);
    if (seen.has(key)) continue;
    seen.add(key);
    identities.push(identity);
  }
  return identities;
}

/** @param {unknown} identities @param {"STOCK"|"TOPIC"} [entityType] */
export function serializeFavoriteIdentities(identities, entityType = FAVORITE_ENTITY_TYPES.STOCK) {
  return JSON.stringify({
    version: FAVORITES_SCHEMA_VERSION,
    items: normalizeFavoriteIdentities(identities, entityType),
  });
}

export function favoriteIdentityKey(identity) {
  return `${normalizeEntityType(identity?.entityType)}:${String(identity?.stableId ?? "").trim()}`;
}

export function favoriteIdentityMatches(left, right) {
  if (!left || !right || normalizeEntityType(left.entityType) !== normalizeEntityType(right.entityType)) return false;
  if (String(left.stableId ?? "").trim() === String(right.stableId ?? "").trim()) return true;
  if (normalizeEntityType(left.entityType) !== FAVORITE_ENTITY_TYPES.STOCK) return false;
  const leftMarket = stockMarketFromStableId(left.stableId);
  const rightMarket = stockMarketFromStableId(right.stableId);
  return !leftMarket || !rightMarket
    ? stockCodeFromStableId(left.stableId) === stockCodeFromStableId(right.stableId)
    : false;
}

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
