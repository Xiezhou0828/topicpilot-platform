"use client";

import { AlertTriangle, DatabaseZap, RefreshCw } from "lucide-react";

export function LoadingState({ label = "正在讀取資料模型" }: { label?: string }) {
  return (
    <section className="state-panel loading-state" role="status" aria-live="polite">
      <span className="state-icon"><DatabaseZap size={22} aria-hidden="true" /></span>
      <div><strong>{label}</strong><p>正在等待 FastAPI 回應並驗證資料格式…</p></div>
      <span className="loading-line" aria-hidden="true" />
    </section>
  );
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <section className="state-panel error-state" role="alert">
      <span className="state-icon"><AlertTriangle size={22} aria-hidden="true" /></span>
      <div>
        <strong>資料服務暫時沒有回應</strong>
        <p>{error.message}</p>
        <small>Render 免費服務可能正在冷啟動，通常需要約一分鐘；本頁不會以假資料默默取代失敗結果。</small>
      </div>
      <button className="button secondary" type="button" onClick={onRetry}><RefreshCw size={16} />重新嘗試</button>
    </section>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <section className="state-panel empty-state" role="status">
      <span className="state-icon">—</span>
      <div><strong>{title}</strong><p>{description}</p></div>
    </section>
  );
}

export function DataOriginNotice({ origin, warning }: { origin: "api" | "demo" | null; warning: string | null }) {
  if (!origin) return null;
  return (
    <div className={`origin-notice ${origin}`} role={warning ? "status" : undefined}>
      <span>{origin === "api" ? "LIVE API" : "SYNTHETIC FALLBACK"}</span>
      <p>{warning ?? "資料由 runtime FastAPI 提供，前端未直接連接正式 Google Sheets。"}</p>
    </div>
  );
}
