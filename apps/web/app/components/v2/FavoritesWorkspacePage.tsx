"use client";

import Link from "next/link";
import { ChevronRight, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useFavoritesState, useTopicFavoritesState } from "../FavoriteButton";
import { fetchFormalStocks, type StockApiItem, type StockApiResource } from "../../lib/stock-api";
import { fetchTopic, fetchTopics, scoreLabel, type TopicDetail, type TopicResource, type TopicSummary } from "../../lib/topic-api";
import { useSnapshot } from "../../lib/snapshot-store";
import type { StockView } from "../../lib/types";
import { AppShell, Card, EmptyState, PageContainer } from "./V2Foundation";
import { StockEncyclopediaDrawer, type StockDrawerItem } from "./StockEncyclopediaDrawer";

type Tab = "topics" | "stocks";
type SavedStock = StockDrawerItem & { mainTopicRole: string | null; updateMode: string; source: "api" | "preview" | "missing" };

const changeLabel = (value: number | null) => value === null ? "—" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
const freshnessLabel = (mode: string, freshness: string | null) => mode === "INTRADAY" || /LIVE|CURRENT|INTRADAY/i.test(freshness ?? "") ? "LIVE" : mode === "POST_CLOSE" || /EOD|POST/i.test(freshness ?? "") ? "EOD" : "資料待更新";
const directionLabel = (value: string | null) => value === "up" ? "持續轉強" : value === "down" ? "今日轉弱" : value === "flat" ? "維持原狀" : "今日變化尚未提供";

function formalStock(item: StockApiItem): SavedStock {
  const primary = item.topicRelations[0] ?? null;
  return { code: item.code, name: item.name ?? item.code, price: item.price, changePct: item.changePct, dataFreshness: item.dataFreshness, updatedAt: item.retrievedAt, topics: item.topicRelations.map((topic) => ({ name: topic.topicName, role: topic.topicRole })), mainTopic: item.mainTopic, mainTopicRole: primary?.topicRole ?? null, updateMode: item.updateMode, source: "api" };
}

function previewStock(item: StockView): SavedStock {
  const primary = item.relations[0] ?? null;
  return { code: item.code, name: item.name ?? item.code, price: item.price, changePct: item.change, dataFreshness: item.dataFreshness, dataDate: item.dataDate, updatedAt: item.updatedAt, topics: item.relations.map((topic) => ({ name: topic.topic, role: topic.role })), mainTopic: item.topicMain ? { name: item.topicMain } : null, mainTopicRole: primary?.role ?? null, updateMode: /LIVE|CURRENT|INTRADAY/i.test(item.dataFreshness ?? "") ? "INTRADAY" : "POST_CLOSE", source: "preview", isPreview: true };
}

export default function FavoritesWorkspacePage() {
  const { bundle } = useSnapshot();
  const { codes, ready: stocksReady } = useFavoritesState();
  const { slugs, ready: topicsReady, toggle: toggleTopic } = useTopicFavoritesState();
  const [tab, setTab] = useState<Tab>("topics");
  const [topicResource, setTopicResource] = useState<TopicResource<TopicSummary[]> | null>(null);
  const [topicDetails, setTopicDetails] = useState<Record<string, TopicDetail | null>>({});
  const [stockResource, setStockResource] = useState<StockApiResource | null>(null);
  const [selectedStock, setSelectedStock] = useState<SavedStock | null>(null);

  useEffect(() => { let active = true; fetchTopics().then((value) => { if (active) setTopicResource(value); }); fetchFormalStocks().then((value) => { if (active) setStockResource(value); }); return () => { active = false; }; }, []);
  useEffect(() => { let active = true; Promise.all(slugs.map(async (slug) => [slug, (await fetchTopic(slug)).data] as const)).then((pairs) => { if (active) setTopicDetails(Object.fromEntries(pairs)); }); return () => { active = false; }; }, [slugs]);
  useEffect(() => { const close = (event: KeyboardEvent) => { if (event.key === "Escape") setSelectedStock(null); }; document.addEventListener("keydown", close); return () => document.removeEventListener("keydown", close); }, []);

  const topics = useMemo(() => { const bySlug = new Map((topicResource?.data ?? []).map((item) => [item.slug, item])); return slugs.map((slug) => ({ slug, summary: bySlug.get(slug) ?? null, detail: topicDetails[slug] ?? null })); }, [slugs, topicDetails, topicResource]);
  const stocks = useMemo(() => { const formal = new Map((stockResource?.data ?? []).map((item) => [item.code, formalStock(item)])); const preview = new Map(bundle.stockUniverse.map((item) => [item.code, previewStock(item)])); return codes.map((code) => formal.get(code) ?? (stockResource?.source === "api" ? null : preview.get(code)) ?? { code, name: code, price: null, changePct: null, dataFreshness: null, topics: [], mainTopic: null, mainTopicRole: null, updateMode: "UNKNOWN", source: "missing" as const }); }, [bundle.stockUniverse, codes, stockResource]);
  const preview = topicResource?.source === "synthetic-snapshot" || stockResource?.source === "synthetic-snapshot";
  const changes = useMemo(() => [
    ...topics.filter((item) => item.summary?.direction).map((item) => ({ key: `t-${item.slug}`, name: item.summary?.name ?? item.slug, value: directionLabel(item.summary?.direction ?? null), kind: "題材" })),
    ...stocks.filter((item): item is SavedStock => item !== null && item.changePct !== null).map((item) => ({ key: `s-${item.code}`, name: item.name, value: `今日 ${changeLabel(item.changePct)}`, kind: "股票" })),
  ].slice(0, 5), [stocks, topics]);
  const ready = stocksReady && topicsReady && topicResource !== null && stockResource !== null;

  return <AppShell currentPath="/favorites"><PageContainer title="我的收藏" description="Watchlist + Market Context：快速查看已收藏題材與股票目前的正式狀態。" className="tp-favorites-page">
    {preview && <p className="tp-favorites-disclosure"><b>Preview</b> · 未設定正式 API origin 的資料區域使用既有公開 snapshot；正式欄位為空時不以 Preview 覆蓋。</p>}
    <section className="tp-favorites-changes" aria-labelledby="favorite-changes-title"><div className="tp-favorites-section-heading"><div><p className="tp-overline">Market Context</p><h2 id="favorite-changes-title">今日有變化</h2></div><span>僅列收藏項目的客觀狀態</span></div>{changes.length ? <div className="tp-favorites-change-list">{changes.map((item) => <div key={item.key}><span className="tp-favorites-change-kind">{item.kind}</span><strong>{item.name}</strong><b>{item.value}</b></div>)}</div> : <p className="tp-favorites-quiet">目前沒有可確認的今日狀態變化。</p>}</section>
    <div className="tp-favorites-tabs" role="tablist" aria-label="收藏類型"><button type="button" role="tab" aria-selected={tab === "topics"} className={tab === "topics" ? "is-active" : ""} onClick={() => setTab("topics")}>題材 <span>{slugs.length}</span></button><button type="button" role="tab" aria-selected={tab === "stocks"} className={tab === "stocks" ? "is-active" : ""} onClick={() => setTab("stocks")}>股票 <span>{codes.length}</span></button></div>
    {!ready ? <Card><p className="tp-favorites-quiet">正在讀取收藏資料…</p></Card> : tab === "topics" ? <section aria-label="收藏題材">{topics.length ? <div className="tp-favorites-table"><div className="tp-favorites-topic-head" aria-hidden="true"><span>題材</span><span>Grade / Score</span><span>生命週期</span><span>今日變化</span><span /></div>{topics.map(({ slug, summary, detail }) => <div className="tp-favorites-topic-row" key={slug}><Link href={`/topics/${slug}`}><span><strong>{summary?.name ?? slug}</strong><small>{summary?.groupName ?? "分類尚未提供"}</small></span><span><b className="tp-favorites-grade">{summary?.grade ?? "—"}</b><em>{scoreLabel(summary?.score ?? null)}</em></span><span>{detail?.lifecycle.currentStage ? <><b>{detail.lifecycle.currentStage}</b>{detail.lifecycle.currentStageTradingDays !== null && <small>Day {detail.lifecycle.currentStageTradingDays}</small>}</> : <small>尚未提供</small>}</span><span>{directionLabel(summary?.direction ?? null)}</span><ChevronRight size={17} aria-hidden="true" /></Link><button type="button" className="tp-favorites-remove" aria-label={`取消收藏 ${summary?.name ?? slug}`} onClick={() => toggleTopic(slug)}><Star size={17} fill="currentColor" aria-hidden="true" /></button></div>)}</div> : <EmptyState title="尚未收藏題材" description="前往題材頁，使用星號加入想持續追蹤的市場題材。" />}</section> : <section aria-label="收藏股票">{stocks.length ? <div className="tp-favorites-table"><div className="tp-favorites-stock-head" aria-hidden="true"><span>股票</span><span>現價</span><span>今日</span><span>主要題材</span><span>角色</span><span>更新</span></div>{stocks.map((stock) => stock && <button type="button" className="tp-favorites-stock-row" key={stock.code} onClick={() => setSelectedStock(stock)}><span><strong>{stock.name}</strong><small>{stock.code}</small></span><b>{stock.price === null ? "—" : stock.price.toLocaleString("zh-TW", { maximumFractionDigits: 2 })}</b><b className={stock.changePct === null ? "" : stock.changePct >= 0 ? "is-up" : "is-down"}>{changeLabel(stock.changePct)}</b><span>{stock.mainTopic?.name ?? stock.topics[0]?.name ?? "尚未提供"}</span><span>{stock.mainTopicRole ?? "—"}</span><span className="tp-favorites-freshness">{freshnessLabel(stock.updateMode, stock.dataFreshness)}</span></button>)}</div> : <EmptyState title="尚未收藏股票" description="前往股票頁，將想持續查看的股票加入收藏。" />}</section>}
    {selectedStock && <StockEncyclopediaDrawer stock={selectedStock} onClose={() => setSelectedStock(null)} />}
  </PageContainer></AppShell>;
}
