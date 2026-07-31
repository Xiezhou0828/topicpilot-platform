"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AppNav } from "./components/AppNav";
import { EmptyState } from "./components/EmptyState";
import { useHomeData, useSnapshot } from "./lib/snapshot-store";
import type { MarketDecisionEvidenceView, MarketDecisionTopicView, StrategyPerformanceView } from "./lib/types";

const healthMetrics = [
  { code: "BREADTH_ADVANCE", label: "上漲股票占比", description: "有效觀察股票中，目前上漲股票所占比例。" },
  { code: "ABOVE_MA60", label: "站上季線比例", description: "有效觀察股票中，收盤價位於 60 日均線之上的比例。" },
  { code: "RS20_POSITIVE", label: "近 20 日強於大盤", description: "有效觀察股票中，近 20 日表現優於加權指數的比例。" },
  { code: "MACD_POSITIVE", label: "MACD 偏多比例", description: "後端判定 MACD 處於偏多狀態的有效股票比例。" },
] as const;

const strategyLogicCopy: Record<string, { short: string; detail: string }> = {
  MAS: { short: "均線結構與相對強度同步轉強。", detail: "以均線結構、趨勢狀態與相對強度篩選合成資料中的候選股。" },
  MAV: { short: "均線趨勢搭配量價確認。", detail: "在趨勢成立後，再用成交量與價格表現確認候選。" },
  TMC: { short: "題材動能與個股表現同步。", detail: "同時檢查題材升溫、個股相對強度與題材關聯。" },
  BB: { short: "整理底部後的突破候選。", detail: "辨識整理區間與突破條件，保留失效價可明確定義的候選。" },
  PB: { short: "趨勢中的受控回檔。", detail: "尋找原有趨勢仍在、回檔幅度與支撐可控的候選。" },
  KD: { short: "KD 指標的中低檔修復。", detail: "以擺盪指標回升作為觀察條件，不把單一指標視為買進訊號。" },
  trend_continuation: { short: "趨勢與動能偏強，取完整排名前 10%。", detail: "趨勢與動能同時偏強的股票，在當日完整排名中取前 10% 作為候選。前 10% 指當日可分析股票的完整排名前 10%。" },
  breakout_volume: { short: "接近或確認突破，量價表現支持。", detail: "股價位階接近或確認突破，且成交量與價格表現支持突破的股票。前 10% 指當日可分析股票的完整排名前 10%。" },
  pullback_timing: { short: "既有趨勢中的回檔時點與量縮條件。", detail: "尋找既有趨勢中的回檔時點，搭配擺盪位置與回檔量縮條件。前 10% 指當日可分析股票的完整排名前 10%。" },
  topic_chip: { short: "題材強度與籌碼資料需同步符合。", detail: "題材強度與籌碼資料同步符合條件；任一必要資料不足時不補假值。前 10% 指當日可分析股票的完整排名前 10%。" },
  risk_first: { short: "先篩風險與可執行性，再排序。", detail: "先用風險與可執行性條件篩選，再在符合者中排序；不把風險分數當作報酬預測。前 10% 指當日可分析股票的完整排名前 10%。" },
  current_composite: { short: "沿用既有正式 Trading／Entry／Daily 規則。", detail: "沿用既有 Trading／Entry／Daily 的正式規則，顯示今日交易觀察結果。" },
};

function price(value: number | null, label?: string | null) {
  if (value !== null) return value.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return label?.trim() || "資料不足";
}

function evidenceRatio(evidence: MarketDecisionEvidenceView | undefined) {
  if (!evidence || evidence.count === null || evidence.denominator === null) return "資料不足";
  return `${evidence.count} / ${evidence.denominator}`;
}

function evidencePct(evidence: MarketDecisionEvidenceView | undefined) {
  return !evidence || evidence.pct === null ? "資料不足" : `${evidence.pct.toFixed(2)}%`;
}

function topicChange(topic: MarketDecisionTopicView) {
  return topic.change14d === null ? null : `${topic.change14d > 0 ? "+" : ""}${topic.change14d.toFixed(2)}`;
}

function taiwanDateParts(value: string | null | undefined) {
  const parsed = value && /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T12:00:00+08:00`) : value ? new Date(value) : new Date();
  if (Number.isNaN(parsed.getTime())) return "日期未提供";
  const parts = new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Taipei", year: "numeric", month: "numeric", day: "numeric", weekday: "short" }).formatToParts(parsed);
  return Object.fromEntries(parts.map((part) => [part.type, part.value]));
}

function taiwanDate(value: string | null | undefined) {
  const values = taiwanDateParts(value);
  if (typeof values === "string") return values;
  const weekday = { Sun: "日", Mon: "一", Tue: "二", Wed: "三", Thu: "四", Fri: "五", Sat: "六" }[values.weekday ?? ""] ?? "—";
  return `${values.year} 年 ${values.month} 月 ${values.day} 日（${weekday}）`;
}

function monthDay(value: string | null | undefined) {
  const values = taiwanDateParts(value);
  return typeof values === "string" ? "資料日未提供" : `${values.month} 月 ${values.day} 日`;
}

function isSameTaiwanDay(value: string | null | undefined) {
  const target = taiwanDateParts(value);
  const current = taiwanDateParts(undefined);
  return typeof target !== "string" && typeof current !== "string" && target.year === current.year && target.month === current.month && target.day === current.day;
}

function publicMarketStatus(dataState: string, marketSession: string | null) {
  if (dataState === "STALE") return "資料延遲";
  if (dataState === "UNAVAILABLE" || dataState === "ERROR") return "資料尚未更新";
  const labels: Record<string, string> = {
    OPEN: "盤中",
    CLOSED: "已收盤",
    HOLIDAY: "休市",
    PREOPEN: "開盤前",
    SUSPENDED: "暫停交易",
  };
  return labels[marketSession ?? ""] ?? "資料已更新";
}

function performanceSummary(performance: StrategyPerformanceView | undefined) {
  if (!performance) return "績效資料尚未提供";
  const matured = performance.horizons.filter((item) => ["COMPLETE", "MATURE"].includes(item.status ?? "") && (item.sampleCount ?? performance.sampleCount) !== null);
  if (!matured.length) return "樣本累積中";
  return matured.map((item) => `${item.horizon} ${item.returnPct === null ? "成熟樣本" : `${item.returnPct > 0 ? "+" : ""}${item.returnPct.toFixed(2)}%`}（${item.sampleCount ?? performance.sampleCount}）`).join(" · ");
}

export default function Home() {
  const home = useHomeData();
  const { bundle, status, refresh } = useSnapshot();
  const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const live = status.dataState === "LIVE" || (status.dataState === "SNAPSHOT" && bundle.marketDecision !== null);
  const freshness = bundle.qualityPanelData.freshness;
  const availableIndices = home.marketIndices.filter((item) => !item.pending).slice(0, 2);
  const topTopics = bundle.source === "snapshot" ? bundle.topics.filter((topic) => topic.strengthScore !== null).slice(0, 3) : [];
  const selectedStrategyId = searchParams.get("strategy");
  const strategyRegistry = bundle.strategyRegistry;
  const selectedStrategy = strategyRegistry?.strategies.find((item) => item.strategyId === selectedStrategyId) ?? null;
  const selectedCandidates = selectedStrategy ? bundle.strategyCandidates.filter((item) => item.strategyId === selectedStrategy.strategyId) : [];
  const performanceByStrategyId = new Map(bundle.strategyPerformance.map((item) => [item.strategyId, item]));
  const decision = bundle.marketDecision;
  const evidenceByCode = new Map((decision?.evidence ?? []).filter((evidence) => evidence.code !== null).map((evidence) => [evidence.code, evidence]));
  const warmingTopics = decision?.topicRotationSummary.topWarming ?? [];
  const coolingTopics = decision?.topicRotationSummary.topCooling ?? [];
  const marketState = live ? decision?.state.label ?? "市場資料尚未更新" : "市場資料尚未更新";
  const observationMode = live ? decision?.observationMode.label ?? "市場資料尚未更新，目前只能查看最近一次題材與股票資料。" : "暫停判讀，不使用上一個畫面做決策";
  const primaryRisk = live ? decision?.risks[0]?.detail ?? "目前沒有主要風險資料" : "等待市場摘要更新";
  const session = freshness.marketSession ?? status.dataState;
  const publicStatus = publicMarketStatus(status.dataState, freshness.marketSession);
  const isStale = status.dataState === "STALE";
  const sameDay = isSameTaiwanDay(freshness.priceAsOf);
  const sessionText = String(session).toUpperCase();
  const freshnessText = isStale
    ? `資料延遲，以下為 ${monthDay(freshness.priceAsOf)}收盤資料`
    : !sameDay || sessionText === "HOLIDAY"
      ? `行情更新至 ${monthDay(freshness.priceAsOf)}收盤`
      : sessionText === "OPEN"
        ? `盤中更新・${freshness.quoteUpdatedAt ?? "時間未提供"}`
        : `已收盤・更新至 ${freshness.quoteUpdatedAt ?? "時間未提供"}`;

  if (bundle.source !== "snapshot" || status.dataState === "UNAVAILABLE" || status.state === "error") {
    const loading = status.state === "loading";
    return <main><AppNav /><div className="appShell liveWorkspace"><header className="topbar marketTopbar homeFocusTopbar"><div><h1>今日市場焦點</h1><p className="homeDate">{taiwanDate(undefined)}・{loading ? "資料載入中" : publicStatus}</p></div></header><EmptyState title={loading ? "資料載入中" : "市場資料尚未更新"} description={loading ? "正在更新市場摘要，完成前不提供替代判斷。" : "目前無法提供市場結論，請在資料更新後再查看。"} onRetry={() => refresh("manual")} retrying={loading} actions={[{ href: "/watchlist", label: "前往股票一覽" }, { href: "/guide", label: "查看使用指南" }]} /></div></main>;
  }

  return (
    <main>
      <AppNav />
      <div className="appShell liveWorkspace homeFocusWorkspace">
        <header className="topbar marketTopbar homeFocusTopbar">
          <div><h1>今日市場焦點</h1><p className="homeDate">{taiwanDate(undefined)}・{publicStatus}</p></div>
          <p className={`homeFreshness ${isStale ? "stale" : ""}`}>{freshnessText}</p>
        </header>

        <section className="homeIndexGrid" aria-label="主要市場指數">
          {availableIndices.map((item) => <article className={`indexPill ${item.stance}`} key={item.name}><span>{item.name}</span><strong>{item.value}</strong><em>{item.subLabel ?? item.asOf ?? "漲跌資料未提供"}</em></article>)}
          {!availableIndices.length && <p className="emptyText">本次分析未提供主要市場指數。</p>}
        </section>

        <section id="market-overview" className="marketJudgement panel" aria-label="今日市場判斷">
          <div className="sectionHead compact"><div><h2>今日市場判斷</h2><p>先確認整體環境，再決定是否觀察候選股。</p></div></div>
          <div className="marketJudgementSummary"><div><b>市場狀態</b><strong>{marketState}</strong></div><div><b>今日操作方式</b><strong>{observationMode}</strong></div><div><b>主要風險</b><strong>{primaryRisk}</strong></div></div>
          <div className="marketHealth"><h3>市場健康度</h3><div className="marketEvidenceGrid">
            {healthMetrics.map((metric) => {
              const evidence = evidenceByCode.get(metric.code);
              const expanded = expandedEvidence === metric.code;
              return <article className={`marketEvidenceCard ${String(evidence?.signal ?? "UNAVAILABLE").toLowerCase()}`} key={metric.code}>
                <div className="evidenceTitle"><span>{metric.label}</span><button type="button" aria-label={`說明：${metric.label}`} aria-expanded={expanded} aria-controls={`evidence-${metric.code}`} onClick={() => setExpandedEvidence(expanded ? null : metric.code)}>?</button></div>
                <strong>{evidencePct(evidence)}</strong><small>{evidenceRatio(evidence)} · {evidence?.signal === "POSITIVE" ? "偏正向" : evidence?.signal === "NEGATIVE" ? "偏負向" : evidence?.signal === "NEUTRAL" ? "中性" : "資料不足"}</small>
                {expanded && <p id={`evidence-${metric.code}`} className="evidenceHelp">{metric.description}</p>}
              </article>;
            })}
          </div></div>
        </section>

        <section className="topicRotationFocus panel" aria-label="題材輪動">
          <div className="sectionHead compact"><div><h2>題材輪動</h2><p>從最強題材開始，再看資金正在流向或撤離哪裡。</p></div><Link href="/topics">查看全部題材</Link></div>
          <div className="topicRotationGrid">
            <div className="topicRotationColumn strongest"><h3>目前最強</h3>{topTopics.length ? topTopics.map((topic, index) => <Link href={`/topics?topic=${encodeURIComponent(topic.name)}`} key={topic.name}><span className="topicRank">{index + 1}</span><b>{topic.name}</b><span className={`grade grade${topic.childGrade ?? topic.grade}`}>{topic.childGrade ?? topic.grade ?? "—"}</span>{topic.strengthScore !== null && <em>{topic.strengthScore.toFixed(2)}</em>}</Link>) : <p className="emptyText">目前沒有題材強度資料。</p>}</div>
            <div className="topicRotationColumn warming"><h3><span aria-hidden="true">↗</span> 正在升溫</h3>{warmingTopics.length ? warmingTopics.map((topic) => <Link href={`/topics?topic=${encodeURIComponent(topic.topic)}`} key={topic.topic}><b>{topic.topic}</b><span>{topicChange(topic) && `14 日 ${topicChange(topic)} · `}{topic.grade ?? "—"}</span></Link>) : <p className="emptyText">目前沒有升溫題材資料。</p>}</div>
            <div className="topicRotationColumn cooling"><h3><span aria-hidden="true">↘</span> 正在降溫</h3>{coolingTopics.length ? coolingTopics.map((topic) => <Link href={`/topics?topic=${encodeURIComponent(topic.topic)}`} key={topic.topic}><b>{topic.topic}</b><span>{topicChange(topic) && `14 日 ${topicChange(topic)} · `}{topic.grade ?? "—"}</span></Link>) : <p className="emptyText">目前沒有降溫題材資料。</p>}</div>
          </div>
        </section>

        <section id="strategy-candidates" className="panel strategyCandidatesPanel" aria-label="策略候選股">
          <div className="sectionHead quoteSectionHead"><div><h2>策略候選股</h2><p>選擇策略查看當日後端選中的標的與已成熟的績效摘要。</p></div></div>
          {!strategyRegistry && <p className="emptyText">策略契約尚未提供，暫不顯示候選股或績效。</p>}
          {strategyRegistry && <>
            <div className="strategyLabels" aria-label="策略入口">{strategyRegistry.strategies.map((strategy) => <Link className={selectedStrategy?.strategyId === strategy.strategyId ? "selected" : ""} href={`/?strategy=${encodeURIComponent(strategy.strategyId)}#strategy-candidates`} key={strategy.strategyId} aria-current={selectedStrategy?.strategyId === strategy.strategyId ? "page" : undefined}><b>{strategy.name}</b><small>{strategy.batchStatus === "COMPLETE_EMPTY" ? "今日無符合標的" : strategy.batchStatus === "COMPLETE" ? `候選 ${strategy.candidateCount ?? "資料不足"} 檔` : "批次資料不足"}</small><span className="strategyLogicShort">{strategyLogicCopy[strategy.strategyId]?.short ?? "策略說明尚未提供"}</span><em>{strategy.batchDate ?? strategyRegistry.dataDate ?? "資料日未提供"}</em></Link>)}</div>
            {!selectedStrategy && <p className="strategyPrompt">請選擇一個策略入口；同一股票可屬於多個策略，畫面不會合併成單一推薦。</p>}
            {selectedStrategy && <div className="strategyDrilldown" aria-live="polite"><div className="strategyDrilldownHead"><div><h3>{selectedStrategy.name}</h3><p className="strategyLogicDetail">{strategyLogicCopy[selectedStrategy.strategyId]?.detail ?? "策略說明尚未提供"}</p><p>{selectedStrategy.batchDate ?? strategyRegistry.dataDate ?? "資料日未提供"} · {selectedStrategy.batchStatus === "COMPLETE_EMPTY" ? "今日無符合標的" : `候選 ${selectedStrategy.candidateCount ?? "資料不足"} 檔`}</p></div><p className="strategyPerformance">績效摘要：{performanceSummary(performanceByStrategyId.get(selectedStrategy.strategyId))}</p></div>{selectedStrategy.batchStatus === "COMPLETE_EMPTY" ? <p className="emptyText">今日無符合標的。</p> : !selectedCandidates.length ? <p className="emptyText">此策略候選資料未提供，暫不顯示替代清單。</p> : <ol className="strategyCandidateList">{selectedCandidates.map((candidate) => { const hasEntry = candidate.trigger !== null || candidate.support !== null || candidate.invalidation !== null; return <li key={candidate.strategyKey ?? `${candidate.strategyId}-${candidate.code}-${candidate.rank ?? ""}`}><span className="strategyRank">{candidate.rank ?? "—"}</span><div><h4>{candidate.name ?? "未提供名稱"} <small>{candidate.code}</small></h4><p>{candidate.majorGroup ?? "主大族群未提供"} · {candidate.fineTopic ?? "細題材未提供"}</p><p>{candidate.reason ?? "入選原因未提供"} · 策略分數 {candidate.score ?? "資料不足"}</p></div><div><small>現價</small><strong>{price(candidate.price)}</strong><small>{candidate.dataTime ?? candidate.dataDate ?? "資料時間未提供"}</small></div><div className="strategyEntry">{hasEntry ? <><span>觸發 {price(candidate.trigger)}</span><span>支撐 {price(candidate.support)}</span><span>失效 {price(candidate.invalidation)}</span></> : <span>此策略未提供進場價位</span>}</div><small className="strategyMembership">所屬策略：{selectedStrategy.name}</small></li>; })}</ol>}</div>}
          </>}
        </section>
      </div>
    </main>
  );
}
