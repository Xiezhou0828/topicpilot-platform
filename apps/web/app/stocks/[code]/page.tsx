"use client";

import Link from "next/link";
import { use } from "react";
import { AppNav } from "../../components/AppNav";
import { EmptyState } from "../../components/EmptyState";
import { FavoriteButton } from "../../components/FavoriteButton";
import { LiveDataBanner } from "../../components/LiveDataBanner";
import { StockSignalLamps } from "../../components/StockSignalLamps";
import { canShowTradeJudgement, evaluateTriggerState } from "../../lib/live-data.mjs";
import { useSnapshot } from "../../lib/snapshot-store";

function value(number: number | null, suffix = "") {
  return number === null ? "資料不足" : `${number.toLocaleString("zh-TW", { maximumFractionDigits: 2 })}${suffix}`;
}

function signed(number: number | null, suffix = "%") {
  return number === null ? "資料不足" : `${number > 0 ? "+" : ""}${number.toFixed(2)}${suffix}`;
}

export default function StockDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { bundle, status } = useSnapshot();
  const { code } = use(params);
  const stock = bundle.stockUniverse.find((item) => item.code === code);

  if (!stock) {
    return <main><AppNav /><div className="appShell"><LiveDataBanner /><EmptyState title="個股資料：找不到這檔股票的正式資料" description="目前 snapshot 沒有提供這檔股票，畫面不會建立替代內容。" actions={[{ href: "/watchlist", label: "回到股票一覽" }, { href: "/guide", label: "查看使用指南" }]} /></div></main>;
  }

  const row = stock.watch;
  const actionable = canShowTradeJudgement(status.dataState, row?.trigger ?? null, row?.dataFreshness);
  const trigger = evaluateTriggerState({ price: stock.price, trigger: row?.trigger ?? null, invalidation: row?.invalidation ?? null, distance: row?.distance ?? null }, actionable);

  return (
    <main>
      <AppNav />
      <div className="appShell">
        <header className="topbar"><div><p className="eyebrow">Stock detail</p><h1>{stock.name ?? "未提供名稱"} <small>{stock.code}</small></h1></div><div className="topActions"><FavoriteButton code={stock.code} /><Link className="textLink" href="/watchlist">股票一覽</Link></div></header>
        <LiveDataBanner />

        <section className="stockDetailGrid">
          <section className={`panel stockQuoteHero trigger-${trigger.tone}`}>
            <div className="stockQuoteHeroHead"><div><span className="eyebrow">Quote</span><h2>{stock.name ?? "未提供名稱"}</h2><p>{stock.code} · {stock.source ?? "來源待接"} · {stock.dataDate ?? "日期待接"}</p></div><span className={`plainGate ${trigger.tone}`}>{trigger.label}</span></div>
            <div className="stockQuoteNumber"><strong>{value(stock.price)}</strong><span className={stock.change === null ? "flat" : stock.change >= 0 ? "up" : "down"}>{value(stock.change, "%")}</span></div>
            {trigger.tone === "hit" && <div className="triggerAlert">▲ 現價已碰到觸發價，請優先確認失效價、資料狀態與個人風險。</div>}
            {!actionable && <div className="tradeBlockNote">{row?.exceptionMessage ?? (status.dataState === "SNAPSHOT" ? "目前為收盤快照，僅供盤後檢視。" : "目前不提供盤中交易判讀。")}</div>}
            <dl className="tradeMetrics"><div><dt>觸發價</dt><dd>{value(row?.trigger ?? null)}</dd></div><div><dt>距觸發方向／幅度</dt><dd>{actionable ? signed(row?.distance ?? null) : "暫不提供"}</dd></div><div><dt>支撐價</dt><dd>{value(row?.support ?? null)}</dd></div><div><dt>失效價</dt><dd>{value(row?.invalidation ?? null)}</dd></div><div><dt>風險幅度</dt><dd>{value(row?.stopPct ?? null, "%")}</dd></div><div><dt>量能狀態／量比</dt><dd>{stock.volumeRatio === null ? stock.volumeStatus ?? "資料不足" : `${stock.volumeStatus ?? "後端量能"} · ${stock.volumeRatio.toFixed(2)}x`}</dd></div><div><dt>進場條件</dt><dd>{row?.entrySetup ?? "資料不足"}</dd></div><div><dt>進場條件分數</dt><dd>{row?.entryScore ?? "資料不足"}</dd></div><div><dt>觀察資格</dt><dd>{row?.gate ?? "資料不足"}</dd></div><div><dt>觀察資格原因</dt><dd>{row?.gateReason ?? "資料不足"}</dd></div></dl>
            {row?.suggestedAction && <p className="suggestedAction"><b>後端建議動作</b>{row.suggestedAction}</p>}
          </section>

          <aside className="sideColumn"><section className="panel"><p className="eyebrow">Topic coverage</p><h2>題材關聯</h2><div className="topicTagList">{stock.relations.length ? stock.relations.map((relation) => <Link className="topicTag" href="/topics" key={`${relation.topic}-${relation.role ?? ""}`}>{relation.topic}<small>{relation.role ?? relation.relation ?? "關聯"}</small></Link>) : <p className="emptyText">snapshot 尚未提供題材關聯。</p>}</div></section><section className="panel"><p className="eyebrow">Trade context</p><h2>後端提供欄位</h2><div className="checkList"><span>技術型態：{stock.technicalSubtype ?? "資料不足"}</span><span>題材主／副：{stock.topicMain ?? "資料不足"} / {stock.topicSub ?? "資料不足"}</span><span>資料更新：{stock.updatedAt ?? "資料不足"}</span></div></section></aside>

          <section className="panel judgementSummary">
            <div className="sectionHead compact"><div><p className="eyebrow">Evidence summary</p><h2>判讀摘要</h2></div><StockSignalLamps stock={stock} /></div>
            <div className="judgementGroups">
              <article><header><span className="signalLamp neutral"><b>籌</b></span><div><h3>籌碼動向</h3><small>{stock.screener.institutionalAsOf ?? stock.screener.tdccAsOf ?? "日期資料不足"}</small></div></header><dl><div><dt>外資連買</dt><dd>{stock.screener.foreignBuyStreakDays === null ? "資料不足" : `${stock.screener.foreignBuyStreakDays} 日`}</dd></div><div><dt>投信連買</dt><dd>{stock.screener.trustBuyStreakDays === null ? "資料不足" : `${stock.screener.trustBuyStreakDays} 日`}</dd></div><div><dt>法人同步</dt><dd>{stock.screener.institutionsInSync === null ? "資料不足" : stock.screener.institutionsInSync ? "是" : "否"}</dd></div><div><dt>400 張以上持股</dt><dd>{value(stock.screener.largeHolder400Pct, "%")}</dd></div><div><dt>1000 張以上持股</dt><dd>{value(stock.screener.largeHolder1000Pct, "%")}</dd></div><div><dt>大戶週變化</dt><dd>{signed(stock.screener.largeHolderWeeklyChangePp, " pp")}</dd></div></dl>{row?.fundingConfirm && <p>{row.fundingConfirm}</p>}{stock.screener.chipDataGap && <p className="dataGapText">{stock.screener.chipDataGap}</p>}</article>
              <article><header><span className="signalLamp neutral"><b>營</b></span><div><h3>營運動能</h3><small>{stock.fundamental.asOf ?? "日期資料不足"}{stock.fundamental.source ? ` · ${stock.fundamental.source}` : ""}</small></div></header><dl><div><dt>月營收 YoY</dt><dd>{signed(stock.fundamental.revenueYoY)}</dd></div><div><dt>月營收 MoM</dt><dd>{signed(stock.fundamental.revenueMoM)}</dd></div><div><dt>近 3 月 YoY</dt><dd>{signed(stock.fundamental.revenue3mYoY)}</dd></div><div><dt>前期近 3 月 YoY</dt><dd>{signed(stock.fundamental.revenue3mPreviousYoY)}</dd></div></dl>{row?.fundamentalCatalyst ? <p>{row.fundamentalCatalyst}</p> : <p className="dataGapText">未提供營運催化文字；不以 EPS 或其他資料替代。</p>}</article>
              <article><header><span className="signalLamp neutral"><b>險</b></span><div><h3>短線風險</h3><small>{stock.updatedAt ?? stock.dataDate ?? "日期資料不足"}</small></div></header><div className="riskEvidence"><p>{row?.shortRisk ?? stock.riskNote ?? "目前沒有可用的短線風險文字。"}</p>{row?.gateReason && <p><b>觀察資格：</b>{row.gateReason}</p>}{row?.exceptionMessage && <p className="dataGapText">{row.exceptionMessage}</p>}</div></article>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}
