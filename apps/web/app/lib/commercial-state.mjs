export const COMMERCIAL_DATA_STATES = Object.freeze([
  "LOADING", "ERROR", "AVAILABLE", "PUBLISHED", "EMPTY", "PARTIAL",
  "STALE", "UNAVAILABLE", "NOT_APPLICABLE",
]);

const AVAILABLE = new Set(["AVAILABLE", "PUBLISHED", "FORMAL"]);

export function commercialDataState({ transport = "READY", status = null, publication = null, freshness = null, rowCount, reason = null, reasonCode = null } = {}) {
  if (transport === "LOADING") return result("LOADING", reason, reasonCode, false);
  if (transport === "ERROR") return result("ERROR", reason, reasonCode, true);
  const authority = typeof status === "string" ? status.trim().toUpperCase() : null;
  const published = typeof publication === "string" ? publication.trim().toUpperCase() : null;
  const age = typeof freshness === "string" ? freshness.trim().toUpperCase() : null;
  if (authority === "NOT_APPLICABLE") return result("NOT_APPLICABLE", reason, reasonCode, false);
  if (authority === "UNAVAILABLE") return result("UNAVAILABLE", reason, reasonCode, false);
  if (authority === "EMPTY") return result("EMPTY", reason, reasonCode, false);
  if (authority === "PARTIAL") return result("PARTIAL", reason, reasonCode, false);
  if (authority === "STALE") return result("STALE", reason, reasonCode, false);
  const isAvailable = AVAILABLE.has(authority) || (!authority && published === "PUBLISHED");
  if (!isAvailable) return result("UNAVAILABLE", reason, reasonCode, false);
  if (rowCount === 0) return result("EMPTY", reason, reasonCode, false);
  if (age === "STALE") return result("STALE", reason, reasonCode, false);
  return result(published === "PUBLISHED" ? "PUBLISHED" : "AVAILABLE", reason, reasonCode, false);
}

function result(state, reason, reasonCode, retryable) {
  return Object.freeze({ state, reason: reason ?? null, reasonCode: reasonCode ?? null, retryable });
}

export function commercialStateLabel(state) {
  return ({ LOADING: "讀取中", ERROR: "讀取失敗", AVAILABLE: "資料可用", PUBLISHED: "正式發布", EMPTY: "目前沒有結果", PARTIAL: "部分資料", STALE: "資料日期較早", UNAVAILABLE: "尚未提供", NOT_APPLICABLE: "不適用" })[state] ?? "狀態未識別";
}
