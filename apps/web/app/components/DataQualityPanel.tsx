"use client";

// WEB-DATA-QUALITY-001（TASK G）＋ WEB-DATA-STALE-001（TASK I）＋ WEB-DATA-REFRESH-001（TASK H）
// 資料品質與新鮮度面板：顯示各來源資料時間、完整度、缺資料、fallback 來源、交易日過期提示。
// - 資料與「重新整理」皆走單一 loader（useQualityPanel → SnapshotProvider），與首頁/觀察清單同步。
// - 交易日過期判斷在 client mount 後計算（Asia/Taipei），避免 SSR/hydration 不一致。
// - 僅顯示層，不改變任何選股分數 / Gate / 排序。

import { useMemo } from "react";
import { useQualityPanel } from "../lib/snapshot-store";
import { evaluateFreshness, taipeiToday } from "../lib/trading-day.mjs";

function dash(value: string | null | undefined) {
  return value && value.trim() !== "" ? value : "—";
}

export function DataQualityPanel({ compact = false }: { compact?: boolean }) {
  const { data, status, refresh } = useQualityPanel();
  const { source, freshness, quality } = data;
  const isMock = source === "mock";

  const stale = useMemo(() => evaluateFreshness(freshness, taipeiToday()), [freshness]);

  const busy = status.state === "loading";

  return (
    <section className={`panel dataQualityPanel${compact ? " compact" : ""}`} aria-label="資料品質">
      <div className="sectionHead">
        <div>
          <p className="eyebrow">Data quality</p>
          <h2>資料品質與新鮮度</h2>
        </div>
        <span className={`sourceBadge ${isMock ? "mock" : status.dataState.toLowerCase()}`}>
          {isMock ? "示範資料（mock）" : `${status.dataState} / 後端 snapshot`}
        </span>
      </div>

      {freshness.stale && (
        <p className="staleWarn" role="status">⚠ {freshness.staleReason ?? "部分資料可能非最新"}</p>
      )}
      {stale?.anyStale && (
        <div className="staleWarn" role="status">
          {stale.items.filter((i) => i.stale).map((i) => (
            <p key={i.key}>⚠ {i.reason}</p>
          ))}
        </div>
      )}
      {isMock && (
        <p className="fallbackNote">目前為 fallback 示範資料，尚未接上後端 snapshot；下列時間僅為佔位。</p>
      )}

      <div className="qualityDates">
        <span><b>資料時間</b>{dash(freshness.dataDate)}</span>
        <span><b>產生時間</b>{dash(freshness.generatedAt)}</span>
        <span><b>報價</b>{dash(freshness.priceAsOf)}</span>
        <span><b>報價更新</b>{dash(freshness.quoteUpdatedAt)}</span>
        <span><b>報價來源</b>{dash(freshness.quoteSource)}</span>
        <span><b>報價批次</b>{dash(freshness.quoteStatus)}</span>
        <span><b>市場狀態</b>{dash(freshness.marketSession)}</span>
        <span><b>最近交易日</b>{dash(freshness.latestTradingDate)}</span>
        <span><b>技術</b>{dash(freshness.technicalAsOf)}</span>
        <span><b>法人</b>{dash(freshness.institutionalAsOf)}</span>
        <span><b>大戶(TDCC)</b>{dash(freshness.tdccAsOf)}</span>
        <span><b>基本面</b>{dash(freshness.fundamentalYm)}</span>
      </div>

      <p className="completenessLine"><b>資料完整度</b>：{freshness.completeness}</p>

      {quality && (
        <div className="qualityMissing">
          <span className={quality.missingEntry > 0 ? "warn" : "ok"}>
            Gate/進場：{quality.entryRows} 檔有值{quality.missingEntry > 0 ? `／${quality.missingEntry} 檔待接` : ""}
          </span>
          <span className={quality.missingChip > 0 ? "warn" : "ok"}>
            籌碼：{quality.chipRows} 檔{quality.missingChip > 0 ? `／${quality.missingChip} 檔待接` : ""}
          </span>
          <span className={quality.missingFundamental > 0 ? "warn" : "ok"}>
            基本面：{quality.fundamentalRows} 檔{quality.missingFundamental > 0 ? `／${quality.missingFundamental} 檔待接` : ""}
          </span>
          {quality.unavailableTechnical.length > 0 && (
            <span className="warn">技術未提供：{quality.unavailableTechnical.join("、")}</span>
          )}
        </div>
      )}

      {quality && (quality.dailyObservationSource || quality.entrySource) && (
        <p className="sourceLine">
          來源：今日交易觀察＝{dash(quality.dailyObservationSource)}／進場條件＝{dash(quality.entrySource)}
        </p>
      )}

      {stale && !stale.anyStale && (
        <p className="sourceLine">各來源資料日期已於上方列出；目前無明顯過期（依台灣交易日判斷）。</p>
      )}

      <div className="qualityActions">
        <button type="button" onClick={() => void refresh("manual")} disabled={busy}>
          {busy ? "更新中…" : "重新整理資料"}
        </button>
        {status.message && (
          <span className={`qualityStatus${status.state === "error" ? " error" : ""}`}>{status.message}</span>
        )}
      </div>
    </section>
  );
}
