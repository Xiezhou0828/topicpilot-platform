"use client";

import { useMemo, useState, type CSSProperties, type FormEvent } from "react";
import Image from "next/image";
import { AppNav } from "../components/AppNav";
import { characters, demoScenarios, models, portfolioSnapshots, strategies } from "./studio-fixture";
import { demoOrchestration, fetchDiscussion, requestForScenario } from "./studio-client";
import { assignmentForCharacter, panelAfterCharacterSelect, performanceIdentity, selectCustomTopic } from "./studio-state.mjs";
import { useSnapshot } from "../lib/snapshot-store";
import type { CharacterId, MeetingStage, OrchestrationState, StudioTab } from "./studio-types";

const tabLabels: Record<StudioTab, string> = { meeting: "會議", character: "角色", portfolio: "持股／績效" };
const stageLabels: Record<MeetingStage, string> = { independent: "獨立判斷", debate: "公開辯論", conclusion: "最終結論" };

function sparkline(points: number[]) {
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  return points.map((point, index) => {
    const x = (index / Math.max(1, points.length - 1)) * 100;
    const y = 34 - ((point - min) / range) * 28;
    return x.toFixed(1) + "," + y.toFixed(1);
  }).join(" ");
}

export default function StudioPage() {
  const { bundle } = useSnapshot();
  const [scenarioId, setScenarioId] = useState(demoScenarios[0].id);
  const [selectedCharacterId, setSelectedCharacterId] = useState<CharacterId>("coda");
  const [tab, setTab] = useState<StudioTab>("meeting");
  const [stage, setStage] = useState<MeetingStage>("independent");
  const [customInput, setCustomInput] = useState("");
  const [customTopic, setCustomTopic] = useState<ReturnType<typeof selectCustomTopic> | null>(null);
  const [orchestration, setOrchestration] = useState(() => demoOrchestration(demoScenarios[0]));
  const [orchestrationState, setOrchestrationState] = useState<OrchestrationState>("complete");
  const [lastRequest, setLastRequest] = useState<ReturnType<typeof requestForScenario> | null>(null);

  const scenario = demoScenarios.find((item) => item.id === scenarioId) ?? demoScenarios[0];
  const character = characters.find((item) => item.id === selectedCharacterId) ?? characters[0];
  const assignment = assignmentForCharacter(scenario.assignments, selectedCharacterId);
  const model = models.find((item) => item.id === assignment?.modelId) ?? models[0];
  const strategy = strategies.find((item) => item.id === assignment?.strategyId) ?? strategies[0];
  const portfolio = portfolioSnapshots.find((item) => item.characterId === selectedCharacterId) ?? portfolioSnapshots[0];
  const activeTopic = customTopic?.state === "WAITING_API" ? customTopic.topic : orchestration.events[0]?.topic ?? scenario.title;
  const stageOpinions = useMemo(() => scenario.opinions.filter((opinion) => opinion.stage === stage), [scenario, stage]);
  const remoteStageEvents = useMemo(() => orchestration.events.filter((event) => event.phase === (stage === "independent" ? "INDEPENDENT" : stage === "debate" ? "DEBATE" : "FINAL")), [orchestration.events, stage]);
  const activeEvent = [...orchestration.events].reverse().find((event) => event.characterId === selectedCharacterId) ?? null;
  const displayModel = activeEvent?.modelId ? models.find((item) => item.id === activeEvent.modelId) : model;

  function chooseScenario(nextId: string) {
    setScenarioId(nextId);
    setCustomTopic(null);
    setStage("independent");
    const nextScenario = demoScenarios.find((item) => item.id === nextId) ?? demoScenarios[0];
    setOrchestration(demoOrchestration(nextScenario));
    setOrchestrationState("complete");
    setLastRequest(null);
  }

  function chooseCharacter(id: CharacterId) {
    const next = panelAfterCharacterSelect(id);
    setSelectedCharacterId(next.characterId);
    setTab(next.tab);
  }

  async function submitCustomTopic(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const selected = selectCustomTopic(customInput);
    setCustomTopic(selected);
    setTab("meeting");
    if (selected.state !== "WAITING_API") return;
    const freshness = bundle.qualityPanelData.freshness;
    if (!freshness.snapshotVersion || !freshness.dataDate) {
      setOrchestrationState("unavailable");
      setOrchestration({ state: "unavailable", events: [], request: null, error: "目前沒有可用的市場快照，無法建立 AI 討論。", source: null });
      return;
    }
    const request = requestForScenario(scenario, selected.topic, "LIVE", freshness);
    setLastRequest(request);
    setOrchestrationState("loading");
    setOrchestration({ state: "loading", events: [], request, error: null, source: null });
    const result = await fetchDiscussion(request);
    setOrchestration(result);
    setOrchestrationState(result.state);
    if (result.events.length) setStage(result.events[0].phase === "INDEPENDENT" ? "independent" : result.events[0].phase === "DEBATE" ? "debate" : "conclusion");
  }

  async function retryDiscussion() {
    if (!lastRequest) return;
    setOrchestrationState("loading");
    setOrchestration((previous) => ({ ...previous, state: "loading", error: null }));
    const result = await fetchDiscussion(lastRequest);
    setOrchestration(result);
    setOrchestrationState(result.state);
  }

  return (
    <main className="studioPage">
      <AppNav />
      <div className="pixelStudioShell">
        <header className="pixelStudioHeader">
          <div><p className="eyebrow">After-market AI studio</p><h1>AI投資工作室</h1></div>
          <div className="demoSafety"><strong>{orchestration.source ?? "DEMO"}</strong><span>{orchestration.source === "LIVE" ? "後端事件／非真實投資績效" : "非模型即時生成／非真實投資績效"}</span></div>
        </header>

        <section className="pixelStudioWorkspace">
          <div className="pixelRoom" aria-label="AI 投資工作室像素客廳">
            <Image alt="AI 交易角色使用的夜間像素客廳" height={844} priority src="/studio/studio-room-v2.png" unoptimized width={1008} />
            <div className="roomAmbient roomAmbientLeft" aria-hidden="true" />
            <div className="roomAmbient roomAmbientRight" aria-hidden="true" />
            <div className="crtOverlay" aria-live="polite">
              <span>{orchestration.source ?? "DEMO"} · {orchestrationState === "loading" ? "等待討論事件" : stageLabels[stage]}</span>
              <strong>{activeTopic}</strong>
              <small>非模型即時生成</small>
            </div>
            {characters.map((item) => {
              const itemAssignment = assignmentForCharacter(scenario.assignments, item.id);
              const itemModel = models.find((entry) => entry.id === itemAssignment?.modelId);
              return (
                <button
                  aria-label={"查看 " + item.name + "，目前指派模型 " + (itemModel?.badge ?? "資料不足")}
                  className={"roomCharacterHotspot roomCharacter-" + item.id + " " + (selectedCharacterId === item.id ? "selected" : "")}
                  key={item.id}
                  onClick={() => chooseCharacter(item.id)}
                  style={{ left: item.roomPosition.left, top: item.roomPosition.top, "--agent-color": item.color } as CSSProperties}
                  type="button"
                >
                  <span className="roomCharacterSpriteFrame" aria-hidden="true">
                    <Image alt="" className="roomCharacterSprite" height={512} priority src={item.roomSprite} unoptimized width={item.roomSpriteWidth} />
                  </span>
                  <span className="roomCharacterStatus"><strong>{item.name}</strong><small>{itemModel?.badge}</small></span>
                </button>
              );
            })}
            <Image alt="" aria-hidden="true" className="roomOcclusion roomOcclusionTable" height={844} src="/studio/studio-room-v2.png" unoptimized width={1008} />
            <Image alt="" aria-hidden="true" className="roomOcclusion roomOcclusionSofa" height={844} src="/studio/studio-room-v2.png" unoptimized width={1008} />
            <div className="roomDemoStamp">DEMO 場景 · 待機中</div>
          </div>

          <aside className="studioControlPanel">
            <section className="studioTopicControl">
              <div className="studioPanelTitle"><div><span>今日討論主題</span><strong>{activeTopic}</strong></div><em>{orchestration.source ?? "DEMO"}</em></div>
              <div className="scenarioButtons" aria-label="選擇 DEMO 劇本">
                {demoScenarios.map((item) => (
                  <button className={!customTopic && scenarioId === item.id ? "active" : ""} key={item.id} onClick={() => chooseScenario(item.id)} type="button">{item.shortLabel}</button>
                ))}
              </div>
              <form className="customTopicForm" onSubmit={submitCustomTopic}>
                <label htmlFor="studio-topic-input">自訂討論假設</label>
                <div><input id="studio-topic-input" onChange={(event) => setCustomInput(event.target.value)} placeholder="輸入想討論的盤後假設" value={customInput} /><button type="submit">送出</button></div>
                <small>{customTopic?.message ?? "自訂主題會送至後端；沒有服務時不會以模板冒充 AI 回答。"}</small>
              </form>
            </section>

            <div className="studioTabs" aria-label="AI 工作室檢視" role="tablist">
              {(Object.keys(tabLabels) as StudioTab[]).map((item) => (
                <button aria-selected={tab === item} className={tab === item ? "active" : ""} key={item} onClick={() => setTab(item)} role="tab" type="button">{tabLabels[item]}</button>
              ))}
            </div>

            <div className="studioPanelBody">
              {tab === "meeting" && (
                <section aria-label="DEMO 會議內容">
                  <div className="meetingStages" aria-label="會議階段">
                    {(Object.keys(stageLabels) as MeetingStage[]).map((item) => (
                      <button className={stage === item ? "active" : ""} key={item} onClick={() => setStage(item)} type="button">{stageLabels[item]} {orchestration.events.filter((event) => event.phase === (item === "independent" ? "INDEPENDENT" : item === "debate" ? "DEBATE" : "FINAL")).length > 0 ? "✓" : ""}</button>
                    ))}
                  </div>
                  {orchestrationState === "loading" ? (
                    <div className="waitingApi"><strong>正在等待 AI 討論事件</strong><p>等待模型 API；後端會依序回傳四位角色的獨立判斷、辯論與最終結論。</p></div>
                  ) : orchestrationState !== "complete" && orchestrationState !== "partial" && orchestrationState !== "idle" && !orchestration.events.length ? (
                    <div className="waitingApi"><strong>{orchestration.error ?? "目前沒有可用的 AI 討論服務"}</strong><p>沒有收到正式 AI 結論；你可以重新嘗試，或切換回 DEMO 劇本。</p><button onClick={retryDiscussion} type="button">重新嘗試</button></div>
                  ) : (
                    <div className="meetingFeed">
                      {(orchestration.events.length ? remoteStageEvents : []).map((event) => {
                        const speaker = characters.find((item) => item.id === event.characterId);
                        return (
                          <article key={event.eventId} style={{ "--agent-color": speaker?.color ?? "#d8e7ee" } as CSSProperties}>
                            {speaker ? <Image alt="" height={42} loading="eager" src={speaker.portrait} unoptimized width={42} /> : <span className="meetingModeratorAvatar" aria-hidden="true">AI</span>}
                            <div>
                              <header><strong>{speaker?.name ?? "主持人"}</strong><span>{event.status} · {event.providerId ?? "未提供 Provider"} / {event.modelId ?? "未提供模型"}</span></header>
                              <p>{event.thesis ?? "此角色沒有提供結論。"}</p>
                              <small>風險：{event.risks.length ? event.risks.join("、") : "未提供"} · 資料日：{event.dataDate}</small>
                              {event.status !== "LIVE" && <em>{event.status} · 僅供研究檢視</em>}
                            </div>
                          </article>
                        );
                      })}
                      {!orchestration.events.length && stageOpinions.map((opinion) => {
                        const speaker = characters.find((item) => item.id === opinion.characterId)!;
                        return (
                          <article key={opinion.id} style={{ "--agent-color": speaker.color } as CSSProperties}>
                            <Image alt="" height={42} loading="eager" src={speaker.portrait} unoptimized width={42} />
                            <div><header><strong>{speaker.name}</strong><span>{opinion.stance} · 信心 {opinion.confidence}%</span></header><p>{opinion.summary}</p><small>風險：{opinion.risk}　失效：{opinion.invalidation}</small>{opinion.sealed && <em>第一輪已密封</em>}</div>
                          </article>
                        );
                      })}
                      {stage === "conclusion" && !orchestration.events.length && <div className="meetingConclusion"><strong>會議結論</strong><p>{scenario.conclusion}</p></div>}
                    </div>
                  )}
                </section>
              )}

              {tab === "character" && (
                <section className="characterPanel" aria-label={character.name + " 角色資料"}>
                  <div className="characterIdentity">
                    <Image alt={character.name + " 像素角色頭像"} height={76} loading="eager" src={character.portrait} unoptimized width={76} />
                    <div><span style={{ color: character.color }}>{displayModel?.badge ?? activeEvent?.providerId ?? "未提供模型"}</span><h2>{character.name}</h2><p>{character.visual}</p></div>
                  </div>
                  <dl className="characterFacts">
                    <div><dt>個性</dt><dd>{character.personality}</dd></div><div><dt>說話方式</dt><dd>{character.speakingStyle}</dd></div>
                    <div><dt>會議功能</dt><dd>{character.meetingRole}</dd></div><div><dt>交易優勢</dt><dd>{character.strength}</dd></div>
                    <div><dt>風險偏好</dt><dd>{strategy.riskPreference}</dd></div><div><dt>持有週期</dt><dd>{strategy.holdingPeriod}</dd></div>
                    <div><dt>主要盲點</dt><dd>{character.blindSpot}</dd></div>
                  </dl>
                  <div className="assignmentBox"><span>目前指派</span><strong>{activeEvent?.providerId ?? displayModel?.provider ?? "未提供 Provider"} · {activeEvent?.modelId ?? displayModel?.modelName ?? "未提供模型"}</strong><small>{activeEvent?.modelVersion ?? displayModel?.modelVersion ?? strategy.strategyVersion} · {activeEvent?.dataDate ?? scenario.session.asOf}</small></div>
                </section>
              )}

              {tab === "portfolio" && (
                <section className="portfolioPanel" aria-label={character.name + " DEMO 持股與績效"}>
                  <div className="portfolioHeading"><div><span>{character.name}</span><strong className={portfolio.returnPct >= 0 ? "positive" : "negative"}>{portfolio.returnPct > 0 ? "+" : ""}{portfolio.returnPct.toFixed(1)}%</strong></div><em>DEMO／非真實投資績效</em></div>
                  <div className="studioPerformanceChart" aria-label={character.name + " DEMO 績效曲線"}><svg role="img" viewBox="0 0 100 40"><polyline points={sparkline(portfolio.equity)} /></svg></div>
                  <dl className="portfolioMetrics">
                    <div><dt>超額報酬</dt><dd>{portfolio.excessReturnPct.toFixed(1)}%</dd></div><div><dt>勝率</dt><dd>{portfolio.winRate}%</dd></div>
                    <div><dt>最大回撤</dt><dd>{portfolio.maxDrawdownPct.toFixed(1)}%</dd></div><div><dt>樣本數</dt><dd>{portfolio.sampleSize}</dd></div>
                  </dl>
                  <div className="studioHoldingList">
                    {portfolio.holdings.map((holding) => <div key={holding.code}><span>{holding.name} <small>{holding.code}</small></span><strong>{holding.weight}%</strong><p>{holding.note}</p></div>)}
                  </div>
                  <code>{performanceIdentity(portfolio.modelVersion, portfolio.strategyVersion, portfolio.sessionVersion)}</code>
                </section>
              )}
            </div>
            <footer className="studioPanelFooter">DEMO fixture · 非模型即時生成 · 非投資建議</footer>
          </aside>
        </section>
      </div>
    </main>
  );
}
