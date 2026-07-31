"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { AppNav } from "../components/AppNav";
import { FavoriteButton, useFavoritesState } from "../components/FavoriteButton";
import { LiveDataBanner } from "../components/LiveDataBanner";
import { buildFavoriteEntries, filterFavoriteEntries, groupFavoriteEntries } from "../lib/favorites-view.mjs";
import { useSnapshot } from "../lib/snapshot-store";
import type { StockView } from "../lib/types";

type ViewMode = "all" | "group";

function price(value: number | null) {
  return value === null ? "資料不足" : value.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function volume(value: number | null) {
  return value === null ? "資料不足" : `${Math.round(value).toLocaleString("zh-TW")} 股`;
}

function Lamp({ active, available, label, short }: { active: boolean; available: boolean; label: string; short: string }) {
  const state = !available ? "missing" : active ? "active" : "inactive";
  const stateText = !available ? "資料不足" : active ? "已觸發" : "未觸發";
  return <span aria-label={`${label}：${stateText}`} className={`favoriteLamp ${state}`} title={`${label}：${stateText}`}>{short}<small>{stateText}</small></span>;
}

function FavoriteCard({ stock, code, status, onOpen }: { stock: StockView | null; code: string; status: string; onOpen: () => void }) {
  const unavailable = status === "snapshot-unavailable";
  const missing = status === "missing-stock";
  const quoteHidden = unavailable || missing;
  const exceptional = stock?.dataFreshness === "EXCEPTION";
  const signal = stock?.signalSummary;
  const changeTone = stock?.change === null || stock?.change === undefined ? "flat" : stock.change > 0 ? "up" : stock.change < 0 ? "down" : "flat";

  return (
    <article
      aria-label={`${stock?.name ?? code} 個股明細`}
      className={`favoriteStockCard ${missing || unavailable ? "unavailable" : ""}`}
      onClick={onOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen();
        }
      }}
      role={stock && !unavailable ? "link" : undefined}
      tabIndex={stock && !unavailable ? 0 : -1}
    >
      <div className="favoriteCardTop">
        <div><h3>{stock?.name ?? "目前資料不存在"} <small>{code}</small></h3><p>{stock ? `${stock.relations[0]?.parentGroup ?? "待分類"}／${stock.topicNames.join("、") || "待分類"}` : "保留本機股號，可使用星號移除"}</p></div>
        <span onClick={(event) => event.stopPropagation()} onKeyDown={(event) => event.stopPropagation()}><FavoriteButton code={code} /></span>
      </div>

      {unavailable && <p className="favoriteStatusNote warning">目前無法取得正式行情；本機自選股號仍已保留。</p>}
      {missing && !unavailable && <p className="favoriteStatusNote missing">目前資料不存在</p>}
      {exceptional && !quoteHidden && <p className="favoriteStatusNote warning">{stock?.exceptionMessage ?? "因特殊情況暫停更新報價"}</p>}

      <dl className="favoriteQuoteGrid">
        <div><dt>現價</dt><dd>{quoteHidden ? "資料不足" : price(stock?.price ?? null)}</dd></div>
        <div><dt>漲跌%</dt><dd className={quoteHidden ? "flat" : changeTone}>{quoteHidden || stock?.change === null || stock?.change === undefined ? "資料不足" : `${stock.change > 0 ? "+" : ""}${stock.change.toFixed(2)}%`}</dd></div>
        <div><dt>成交量</dt><dd>{quoteHidden ? "資料不足" : volume(stock?.volume ?? null)}</dd></div>
      </dl>

      <div className="favoriteLampRow" aria-label="籌碼、營運與風險燈號">
        <Lamp active={!quoteHidden && !!signal?.chipActive} available={!quoteHidden && !!signal?.chipAvailable} label="籌碼動向" short="籌" />
        <Lamp active={!quoteHidden && !!signal?.operationsActive} available={!quoteHidden && !!signal?.operationsAvailable} label="營運動能" short="營" />
        <Lamp active={!quoteHidden && !!signal?.riskActive} available={!quoteHidden && !!signal?.riskAvailable} label="短線風險" short="險" />
      </div>
    </article>
  );
}

export default function FavoritesPage() {
  const router = useRouter();
  const { bundle, status } = useSnapshot();
  const { codes, ready } = useFavoritesState();
  const [viewMode, setViewMode] = useState<ViewMode>("all");
  const [query, setQuery] = useState("");
  const hasFormalSnapshot = bundle.source === "snapshot" && bundle.stockUniverse.length > 0;
  const snapshotAvailable = hasFormalSnapshot && status.state !== "error" && status.dataState !== "UNAVAILABLE";
  const entries = useMemo(
    () => buildFavoriteEntries(codes, hasFormalSnapshot ? bundle.stockUniverse : [], snapshotAvailable),
    [codes, hasFormalSnapshot, bundle.stockUniverse, snapshotAvailable],
  );
  const filtered = useMemo(() => filterFavoriteEntries(entries, query), [entries, query]);
  const groups = useMemo(() => groupFavoriteEntries(filtered), [filtered]);
  const dataDate = bundle.qualityPanelData.freshness.dataDate;

  const openStock = (entry: { stock: StockView | null; status: string }) => {
    if (entry.stock && entry.status !== "snapshot-unavailable") router.push(`/stocks/${entry.stock.code}`);
  };

  const renderCards = (items: typeof filtered) => (
    <div className="favoriteCardGrid">
      {items.map((entry) => <FavoriteCard code={entry.code} key={entry.code} onOpen={() => openStock(entry)} status={entry.status} stock={entry.stock} />)}
    </div>
  );

  return (
    <main>
      <AppNav />
      <div className="appShell favoritesWorkspace">
        <header className="topbar favoritesTopbar">
          <div><p className="eyebrow">My watchlist</p><h1>我的觀察</h1><p>只代表你希望持續追蹤，不代表系統推薦、持有或買進。</p></div>
          <div className="topActions"><span>{codes.length} 檔自選</span><strong>{status.dataState}</strong></div>
        </header>

        <LiveDataBanner />

        <section className="panel favoritesSummary" aria-label="我的觀察資料摘要">
          <div><strong>{codes.length}</strong><span>檔保存在目前裝置</span></div>
          <div><small>資料日期</small><b>{dataDate ?? "資料不足"}</b></div>
          <div><small>資料狀態</small><b>{snapshotAvailable ? "正式 snapshot 可用" : "正式行情目前不可用"}</b></div>
          <p>自選資料僅保存在目前裝置；目前不提供帳號綁定、跨裝置同步或備份。</p>
        </section>

        <section className="panel favoritesControls">
          <div className="segmented" aria-label="自選檢視方式" role="group">
            <button className={viewMode === "all" ? "active" : ""} onClick={() => setViewMode("all")} type="button">全部自選</button>
            <button className={viewMode === "group" ? "active" : ""} onClick={() => setViewMode("group")} type="button">依主大族群</button>
          </div>
          <label className="search"><span>搜尋</span><input onChange={(event) => setQuery(event.target.value)} placeholder="股號或名稱" value={query} /></label>
          <Link className="primaryLink" href="/watchlist">回股票一覽新增標的</Link>
        </section>

        {!ready && <section className="panel favoritesEmpty"><h2>正在讀取本機自選</h2><p>請稍候。</p></section>}

        {ready && !codes.length && (
          <section className="panel favoritesEmpty">
            <p className="eyebrow">尚無自選</p><h2>先加入想持續追蹤的股票</h2>
            <p>你可以從股票一覽、題材頁或個股明細按下星號；加入後會立即同步到這個頁面。</p>
            <Link className="primaryLink" href="/watchlist">前往股票一覽</Link>
          </section>
        )}

        {ready && codes.length > 0 && !filtered.length && (
          <section className="panel favoritesEmpty"><h2>搜尋不到自選股票</h2><p>目前自選仍保留，請清除搜尋文字後再查看。</p><button className="clearFilters" onClick={() => setQuery("")} type="button">清除搜尋</button></section>
        )}

        {ready && filtered.length > 0 && viewMode === "all" && <section className="favoritesList" aria-label="全部自選">{renderCards(filtered)}</section>}

        {ready && filtered.length > 0 && viewMode === "group" && (
          <div className="favoriteGroups">
            {groups.map((group) => (
              <section className="panel favoriteGroup" key={group.name}>
                <div className="sectionHead"><div><p className="eyebrow">主大族群</p><h2>{group.name}</h2></div><span>{group.topics.reduce((sum, topic) => sum + topic.items.length, 0)} 檔</span></div>
                {group.topics.map((topic) => <div className="favoriteTopicGroup" key={topic.name}><h3>{topic.name}</h3>{renderCards(topic.items)}</div>)}
              </section>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
