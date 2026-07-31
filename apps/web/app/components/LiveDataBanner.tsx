"use client";

import { useSnapshot } from "../lib/snapshot-store";

const labels = {
  LOADING: "更新中",
  LIVE: "資料可用",
  SNAPSHOT: "收盤快照",
  STALE: "資料已過期",
  ERROR: "讀取失敗",
  UNAVAILABLE: "資料不足",
} as const;

function displayTime(value: string | null) {
  if (!value) return null;
  if (!value.includes("T")) return value;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("zh-TW", {
    timeZone: "Asia/Taipei",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function LiveDataBanner() {
  const { bundle, status, refresh } = useSnapshot();
  const freshness = bundle.qualityPanelData.freshness;
  const busy = status.dataState === "LOADING";

  return (
    <section className={`liveDataBanner state${status.dataState}`} aria-live="polite">
      <div className="liveStateMark" aria-hidden="true" />
      <div className="liveDataCopy">
        <div>
          <strong>{labels[status.dataState]}</strong>
          <span>{status.message ?? "正在確認後台資料狀態。"}</span>
        </div>
        <small>
          報價 {freshness.priceAsOf ?? "無時間"}
          {freshness.quoteUpdatedAt ? ` ${displayTime(freshness.quoteUpdatedAt)}` : ""}
          {` / 來源 ${freshness.quoteSource ?? freshness.sourceLabel}`}
          {freshness.marketSession ? ` / 市場 ${freshness.marketSession}` : ""}
          {status.lastSuccessAt ? ` / 前端最後成功 ${new Date(status.lastSuccessAt).toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit" })}` : ""}
        </small>
      </div>
      <button type="button" onClick={() => void refresh("manual")} disabled={busy}>
        {busy ? "更新中" : "重新整理"}
      </button>
    </section>
  );
}
