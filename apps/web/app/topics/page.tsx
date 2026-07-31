"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AppNav } from "../components/AppNav";
import { EmptyState } from "../components/EmptyState";
import { FavoriteButton } from "../components/FavoriteButton";
import { LiveDataBanner } from "../components/LiveDataBanner";
import { useSnapshot } from "../lib/snapshot-store";
import type { StockView, TopicGroupView, TopicStrengthHistoryView, TopicView } from "../lib/types";

function scoreTone(score: number | null) {
  if (score === null) return "na";
  if (score >= 7.5) return "hot";
  if (score >= 4) return "warm";
  if (score >= -2) return "flat";
  return "cold";
}

function barWidth(score: number | null) {
  if (score === null) return 0;
  return Math.max(4, Math.min(100, (Math.abs(score) / 14) * 100));
}

function sortGroups(groups: TopicGroupView[]) {
  return [...groups].sort((a, b) => (b.score ?? -999) - (a.score ?? -999));
}

function tileSize(index: number) {
  if (index === 0) return "tileXL";
  if (index <= 2) return "tileWide";
  if (index <= 6) return "tileMedium";
  return "tileSmall";
}

function representativeTopic(group: TopicGroupView, topics: TopicView[]) {
  return topics.find((item) => item.name === group.strongestChild)
    ?? topics.find((item) => group.children.includes(item.name))
    ?? null;
}

function tileMeta(group: TopicGroupView, topic: TopicView | null) {
  if (topic?.observedCount !== null && topic?.observedCount !== undefined) {
    return `${topic.observedCount} 檔 · 齊場 ${topic.breadth ?? "—"}`;
  }
  return `${group.scoredChildCount ?? 0}/${group.childCount ?? 0} 細題材有分數`;
}

function historyHeight(score: number | null, points: TopicStrengthHistoryView["points"]) {
  if (score === null) return 10;
  const values = points.map((point) => point.score).filter((value): value is number => value !== null);
  if (!values.length) return 10;
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) return 55;
  return 18 + ((score - min) / (max - min)) * 72;
}

export default function TopicsPage() {
  const searchParams = useSearchParams();
  const { bundle, status, refresh } = useSnapshot();
  const topics = bundle.topics;
  const groups = bundle.topicGroups;
  const stockUniverse = bundle.stockUniverse;
  const [groupSelection, setActiveGroup] = useState<string | null | undefined>(undefined);
  const [topicSelection, setSelectedTopic] = useState<string | undefined>(undefined);
  const requestedGroup = searchParams.get("group") ?? "";
  const requestedTopic = searchParams.get("topic") ?? "";
  const requestedTopicView = topics.find((item) => item.name === requestedTopic);
  const requestedParent = requestedTopic
    ? groups.find((item) => item.children.includes(requestedTopic) || item.name === requestedTopicView?.group)
    : groups.find((item) => item.name === requestedGroup);
  const activeGroup = groupSelection === undefined ? requestedParent?.name ?? null : groupSelection;
  const selectedTopic = topicSelection === undefined
    ? requestedTopic && requestedParent ? requestedTopic : requestedParent?.children[0] ?? ""
    : topicSelection;

  const sortedGroups = useMemo(() => sortGroups(groups), [groups]);
  const group = groups.find((item) => item.name === activeGroup) ?? null;
  const groupTopics = group ? topics.filter((item) => group.children.includes(item.name)) : [];
  const topic = groupTopics.find((item) => item.name === selectedTopic) ?? groupTopics[0] ?? null;
  const relatedStocks: StockView[] = topic
    ? stockUniverse
      .filter((item) => item.topicNames.includes(topic.name) || item.relations.some((relation) => relation.topic === topic.name) || topic.leaders.includes(item.name ?? ""))
      .sort((a, b) => (a.watch?.rank ?? Number.MAX_SAFE_INTEGER) - (b.watch?.rank ?? Number.MAX_SAFE_INTEGER))
    : [];
  const history = topic ? bundle.topicStrengthHistory.find((item) => item.topic === topic.name) : null;

  if (bundle.source !== "snapshot" || status.state === "error" || status.dataState === "UNAVAILABLE") {
    return <main><AppNav /><div className="appShell"><LiveDataBanner /><EmptyState title={status.state === "loading" ? "題材總覽：封測資料尚未載入" : "題材總覽目前尚無可用資料"} description="題材總覽用來比較資金集中方向；正式 snapshot 載入前不顯示示範題材。" onRetry={() => refresh("manual")} retrying={status.state === "loading"} actions={[{ href: "/watchlist", label: "前往股票一覽" }, { href: "/guide", label: "查看使用指南" }]} /></div></main>;
  }

  if (!groups.length) {
    return <main><AppNav /><div className="appShell"><EmptyState title="題材總覽目前沒有可顯示的題材" description="snapshot 已載入，但尚無大族群可比較。可以重新載入或先從股票一覽查看正式股票。" onRetry={() => refresh("manual")} actions={[{ href: "/watchlist", label: "前往股票一覽" }, { href: "/guide", label: "查看使用指南" }]} /></div></main>;
  }

  const openGroup = (name: string) => {
    const next = groups.find((item) => item.name === name);
    setActiveGroup(name);
    setSelectedTopic(next?.children[0] ?? "");
  };

  return (
    <main>
      <AppNav />
      <div className="appShell">
        <header className="topbar">
          <div><p className="eyebrow">Topic overview</p><h1>題材總覽</h1></div>
          <div className="topActions"><span>{group ? "大族群與細題材分開觀察" : "方塊大小＝彙總層級，顏色＝細題材彙總強弱"}</span></div>
        </header>

        <LiveDataBanner />

        {!group && (
          <section className="panel">
            <div className="sectionHead">
              <div><p className="eyebrow">Heat matrix</p><h2>大族群一眼掃完</h2></div>
              <span>方塊大小＝觀察檔數 · 顏色＝強弱 · 點方塊進細題材</span>
            </div>
            <div className="groupMatrix">
              {sortedGroups.map((item, index) => (
                <button
                  aria-label={`查看${item.name}細題材`}
                  className={`groupTile ${scoreTone(item.score)} ${tileSize(index)} ${item.name === activeGroup ? "selected" : ""}`}
                  key={item.name}
                  onClick={() => openGroup(item.name)}
                  type="button"
                >
                  {(() => {
                    const lead = representativeTopic(item, topics);
                    const grade = lead?.childGrade ?? (item.score !== null && item.score >= 7.5 ? "S" : item.score !== null && item.score >= 4 ? "A" : "—");
                    return (
                      <>
                        <span className="tileHead">
                          <span className="tileTitle"><b>{item.name}</b><span className={`grade grade${grade}`}>{grade}</span></span>
                          <em>{item.score === null ? "—" : item.score.toFixed(2)}</em>
                        </span>
                        <strong className="tileScore">{item.score === null ? "—" : item.score.toFixed(2)}</strong>
                        <small>{tileMeta(item, lead)}</small>
                        <small className="tileLead">{item.strengthState ?? "細題材彙總"} · {item.scoredChildCount ?? 0}/{item.childCount ?? 0} 有分數</small>
                        {item.children.length > 1 && (
                          <span className="tileChildren">
                            {item.children.slice(0, 4).map((child) => <span key={child}>{child}</span>)}
                            {item.children.length > 4 && <span>＋{item.children.length - 4}</span>}
                          </span>
                        )}
                      </>
                    );
                  })()}
                </button>
              ))}
            </div>
            <p className="matrixLegend">紅＝強勢（≥7.5）· 黃＝偏強（≥4）· 灰＝中性 · 綠＝弱勢（沿用紅漲綠跌）</p>
          </section>
        )}

        {group && (
          <>
            <div className="groupSwitchBar">
              <button className="backToMatrix" onClick={() => setActiveGroup(null)} type="button">← 題材矩陣</button>
              <div className="groupSwitchList">
                {sortedGroups.map((item) => (
                  <button
                    className={`groupSwitch ${item.name === group.name ? "active" : ""}`}
                    key={item.name}
                    onClick={() => openGroup(item.name)}
                    type="button"
                  >
                    {item.name}<em>{item.score === null ? "—" : item.score.toFixed(2)}</em>
                  </button>
                ))}
              </div>
            </div>

            <section className="topicSplit">
              <section className="panel childTopicPanel">
                <div className="sectionHead compact">
                  <div><p className="eyebrow">Child topics</p><h2>{group.name}</h2></div>
                </div>
                <div className="childTopicList">
                  {groupTopics.map((item) => {
                    const grade = item.childGrade ?? item.grade;
                    return (
                      <button
                        className={`childTopicRow ${topic && item.name === topic.name ? "active" : ""}`}
                        key={item.name}
                        onClick={() => setSelectedTopic(item.name)}
                        type="button"
                      >
                        <span className={`grade grade${grade}`}>{grade}</span>
                        <span className="childTopicBody">
                          <span className="childTopicHead"><strong>{item.name}</strong><em>{item.strengthScore === null ? "—" : item.strengthScore.toFixed(2)}</em></span>
                          <span className={`scoreBar ${scoreTone(item.strengthScore)}`}><i style={{ width: `${barWidth(item.strengthScore)}%` }} /></span>
                          <small>{item.strengthState ?? item.signal ?? "觀察"} · {item.observedCount ?? 0} 筆觀察 · {item.confidence ?? "—"}</small>
                        </span>
                      </button>
                    );
                  })}
                  {!groupTopics.length && <p className="emptyText">此大族群目前沒有細題材資料。</p>}
                </div>
              </section>

              <div className="topicDetailColumn">
                {topic ? (
                  <>
                    <section className="panel topicDetail">
                      <div className="topicHero">
                        <div><p className="eyebrow">Selected topic</p><h2>{topic.name}</h2><p>{topic.note}</p></div>
                        <span className="signalTag">{topic.strengthState ?? topic.signal ?? "觀察"}</span>
                      </div>
                      <div className="miniStats">
                        <article><span>強度分數</span><strong>{topic.strengthScore === null ? "—" : topic.strengthScore.toFixed(2)}</strong></article>
                        <article><span>顯示狀態</span><strong>{topic.strengthState ?? "—"}</strong></article>
                        <article><span>樣本／信心</span><strong>{topic.observedCount ?? 0} / {topic.confidence ?? "—"}</strong></article>
                      </div>
                      {topic.leaders.length > 0 && <div className="leaderDeck">{topic.leaders.map((leader) => <span key={leader}>{leader}</span>)}</div>}
                    </section>

                    <section className="panel topicHistoryPanel">
                      <div className="sectionHead compact"><div><p className="eyebrow">Recent strength</p><h2>近 14 個交易日</h2></div><span>{history?.points.length ? `${history.points[0].date} → ${history.points[history.points.length - 1].date}` : "歷史資料待接"}</span></div>
                      {history?.points.length ? (
                        <div className="topicHistoryChart" aria-label={`${topic.name} 近 14 個交易日強度`}>
                          {history.points.slice(-14).map((point) => <div className="topicHistoryPoint" key={point.date}><div className="topicHistoryBar"><i style={{ height: `${historyHeight(point.score, history.points)}%` }} /></div><strong>{point.score === null ? "—" : point.score.toFixed(2)}</strong><small>{point.date.slice(5)}</small></div>)}
                        </div>
                      ) : <div className="dataContractGap"><strong>後端 snapshot 尚未提供近 14 個交易日題材強度。</strong><span>目前不以單日漲跌或廣度替代，待後端提供實際交易日序列後顯示。</span></div>}
                    </section>

                    <section className="panel">
                      <div className="sectionHead compact"><div><p className="eyebrow">Topic coverage</p><h2>{topic.name} 相關標的</h2></div><span>{relatedStocks.length} 檔</span></div>
                      <div className="relatedList">
                        {relatedStocks.length ? relatedStocks.map((item) => (
                          <article className="relatedRow" key={item.code}>
                            <Link className="relatedIdentity" href={`/stocks/${item.code}`}><strong>{item.name ?? "—"} <small>{item.code}</small></strong><small>{item.watch?.section ?? item.technicalSubtype ?? "股票總覽"}</small></Link>
                            <span className="relatedNum"><small>價格</small><b>{item.price ?? "—"}</b></span>
                            <span className="relatedNum"><small>觸發</small><b>{item.watch?.trigger ?? "—"}</b></span>
                            <span className="relatedNum"><small>距離</small><b>{item.watch?.distance !== null && item.watch?.distance !== undefined ? `${item.watch.distance.toFixed(2)}%` : "—"}</b></span>
                            <span className={`gate gate${item.watch?.gate ?? "NA"}`}>{item.watch?.gate ?? "未列入觀察"}</span>
                            <FavoriteButton code={item.code} />
                          </article>
                        )) : <p className="emptyText">正式 snapshot 沒有提供此題材的股票關聯。</p>}
                      </div>
                    </section>

                    <section className="panel">
                      <p className="eyebrow">Interpretation</p>
                      <h2>如何解讀</h2>
                      <div className="checkList">
                        <span>細題材分數可在小樣本下先行顯示。</span>
                        <span>樣本數、觀察覆蓋率與資料信心度分開呈現，不直接取代題材強度。</span>
                        <span>大族群可由最強細題材與族群分歧判斷輪動。</span>
                      </div>
                    </section>
                  </>
                ) : <section className="panel"><p className="emptyText">請從左側選擇一個細題材。</p></section>}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
