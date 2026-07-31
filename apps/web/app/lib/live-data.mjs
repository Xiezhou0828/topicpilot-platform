import { evaluateStaleness, taipeiToday } from "./trading-day.mjs";

export const LIVE_REFRESH_INTERVAL_MS = 3 * 60_000;

export function evaluateLiveData({ source, dataDate, generatedAt, quoteUpdatedAt, quoteStatus, marketSession, rowCount }, today = taipeiToday()) {
  if (source !== "snapshot" || !dataDate || !generatedAt || !quoteUpdatedAt || !Number.isFinite(rowCount) || rowCount <= 0) {
    return {
      state: "UNAVAILABLE",
      delayedTradingDays: null,
      message: "缺少必要報價時間或觀察資料，暫不提供交易判斷。",
    };
  }

  if (quoteStatus === "PARTIAL") {
    return { state: "UNAVAILABLE", delayedTradingDays: null, message: "本批報價只有部分完成，目前僅供資料追查。" };
  }
  if (quoteStatus === "FAILED" || quoteStatus === "NOT_RUN") {
    return { state: "UNAVAILABLE", delayedTradingDays: null, message: "本批報價尚未完成，目前不提供交易判斷。" };
  }

  // Compare the snapshot date with the current Taiwan trading calendar. The
  // backend's latestTradingDate describes the batch, not the current date;
  // using it here would make an old batch appear fresh indefinitely.
  const freshness = evaluateStaleness({ date: dataDate, today, thresholdDays: 1 });
  if (!freshness.valid) {
    return {
      state: "UNAVAILABLE",
      delayedTradingDays: null,
      message: "無法確認報價日期，暫不提供交易判斷。",
    };
  }

  if (freshness.stale) {
    return {
      state: "STALE",
      delayedTradingDays: freshness.gapTradingDays,
      message: `資料延遲 ${freshness.gapTradingDays} 個交易日，目前不適合盤中交易。`,
    };
  }

  if (marketSession !== "OPEN") {
    return {
      state: "SNAPSHOT",
      delayedTradingDays: 0,
      message: "收盤快照可用，僅供盤後檢視，不提供盤中交易判讀。",
    };
  }

  return {
    state: "LIVE",
    delayedTradingDays: 0,
    message: "盤中報價可用；PASS 只代表符合觀察條件，不代表立即買進。",
  };
}

export function isTaiwanMarketSession(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Taipei",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const byType = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  if (byType.weekday === "Sat" || byType.weekday === "Sun") return false;
  const minutes = Number(byType.hour) * 60 + Number(byType.minute);
  return minutes >= 8 * 60 + 55 && minutes <= 13 * 60 + 35;
}

export function canShowTradeJudgement(dataState, trigger, dataFreshness = "CURRENT") {
  return dataState === "LIVE" && dataFreshness !== "EXCEPTION" && typeof trigger === "number" && Number.isFinite(trigger);
}

export function evaluateTriggerState({ price, trigger, invalidation, distance }, actionable) {
  if (!actionable) return { label: "尚無判讀", detail: "確認資料後再觀察", tone: "disabled" };
  if (typeof price === "number" && typeof invalidation === "number" && price <= invalidation) {
    return { label: "已碰失效價", detail: `失效 ${invalidation}`, tone: "invalid" };
  }
  if (typeof price === "number" && typeof trigger === "number" && price >= trigger) {
    return { label: "已碰觸發價", detail: `觸發 ${trigger}`, tone: "hit" };
  }
  if (typeof distance === "number" && distance >= 0 && distance <= 3) {
    return { label: "接近觸發", detail: `距離 ${distance.toFixed(2)}%`, tone: "near" };
  }
  return {
    label: "等待觸發",
    detail: typeof distance === "number" ? `距離 ${distance.toFixed(2)}%` : "距離資料不足",
    tone: "waiting",
  };
}
