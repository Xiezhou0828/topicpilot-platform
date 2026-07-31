import { characters, models, strategies } from "./studio-fixture";
import type {
  CharacterId,
  DemoScenario,
  DiscussionEvent,
  DiscussionPhase,
  DiscussionRequest,
  OrchestrationState,
  StudioOrchestration,
} from "./studio-types";

const phaseOrder: DiscussionPhase[] = ["INDEPENDENT", "DEBATE", "FINAL"];
const canonicalStrategyByCharacter: Record<CharacterId, string> = {
  coda: "momentum-execution",
  mori: "risk-invalidation",
  prism: "theme-catalyst",
  volt: "event-reversal",
};

export function orchestrationEndpoint() {
  return process.env.NEXT_PUBLIC_AI_STUDIO_ORCHESTRATION_URL?.trim() || null;
}

export function requestForScenario(scenario: DemoScenario, topic = scenario.title, mode: "DEMO" | "LIVE" = "LIVE", snapshot?: { snapshotVersion?: string | null; dataDate?: string | null }): DiscussionRequest {
  return {
    contractVersion: "1.0.0",
    sessionId: `${mode.toLowerCase()}-${scenario.id}-${Date.now()}`,
    topic,
    snapshotVersion: snapshot?.snapshotVersion ?? scenario.session.id,
    dataDate: snapshot?.dataDate ?? "2026-07-18",
    mode,
    participants: scenario.assignments.map((assignment) => {
      const character = characters.find((item) => item.id === assignment.characterId)!;
      return {
        characterId: character.id,
        personaVersion: "1.0.0",
        strategyId: canonicalStrategyByCharacter[character.id],
        strategyVersion: "1.0.0",
        bindingId: character.id,
      };
    }),
    phasePolicy: { order: ["INDEPENDENT", "DEBATE", "FINAL"], independentImmutable: true, appendOnly: true },
  };
}

function demoEvents(scenario: DemoScenario): DiscussionEvent[] {
  return scenario.opinions.map((opinion, index) => {
    const assignment = scenario.assignments.find((item) => item.characterId === opinion.characterId);
    const strategy = strategies.find((item) => item.id === assignment?.strategyId);
    const model = models.find((item) => item.id === assignment?.modelId);
    const phase = opinion.stage === "independent" ? "INDEPENDENT" : opinion.stage === "debate" ? "DEBATE" : "FINAL";
    return {
      contractVersion: "1.0.0",
      eventId: `${scenario.session.id}-${opinion.id}`,
      sessionId: scenario.session.id,
      topic: scenario.title,
      snapshotVersion: scenario.session.id,
      dataDate: scenario.session.asOf,
      phase,
      phaseSequence: index + 1,
      characterId: opinion.characterId,
      personaVersion: "1.0.0",
      strategyId: strategy?.id ?? null,
      strategyVersion: strategy?.strategyVersion ?? null,
      providerId: model?.provider.toLowerCase() ?? "mock",
      modelId: model?.id ?? "mock-model",
      modelVersion: model?.modelVersion ?? "demo-model-v0",
      thesis: opinion.summary,
      evidence: [],
      risks: [opinion.risk, opinion.invalidation].filter(Boolean),
      confidence: opinion.confidence / 100,
      generatedAt: new Date(0).toISOString(),
      latencyMs: 0,
      usage: { inputTokens: 0, outputTokens: 0 },
      status: "DEMO",
      immutable: opinion.sealed,
      parentEventIds: index === 0 ? [] : [scenario.session.id],
      researchOnly: true,
    };
  });
}

function rawEvents(payload: unknown): unknown[] {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];
  const record = payload as Record<string, unknown>;
  if (Array.isArray(record.events)) return record.events;
  if (record.event && typeof record.event === "object") return [record.event];
  return [];
}

function isCharacterId(value: unknown): value is CharacterId | null {
  return value === null || characters.some((character) => character.id === value);
}

export function validateDiscussionEvents(events: unknown[], expectedSessionId?: string): DiscussionEvent[] {
  const ids = new Set<string>();
  let previousPhase = -1;
  let previousSequence = 0;
  return events.map((candidate) => {
    if (!candidate || typeof candidate !== "object") throw new Error("事件格式無法辨識");
    const event = candidate as Partial<DiscussionEvent>;
    if (event.contractVersion !== "1.0.0" || typeof event.eventId !== "string" || ids.has(event.eventId)) throw new Error("事件契約或事件順序無效");
    if (expectedSessionId && event.sessionId !== expectedSessionId) throw new Error("事件 session 不一致");
    if (!phaseOrder.includes(event.phase as DiscussionPhase) || !Number.isInteger(event.phaseSequence) || !isCharacterId(event.characterId)) throw new Error("事件 phase 或角色資料無效");
    const phaseIndex = phaseOrder.indexOf(event.phase as DiscussionPhase);
    if (phaseIndex < previousPhase || (phaseIndex === previousPhase && (event.phaseSequence as number) <= previousSequence)) throw new Error("事件必須依 append-only 順序排列");
    if (!Array.isArray(event.evidence) || !Array.isArray(event.risks) || !["DEMO", "MOCK", "LIVE", "RATE_LIMITED", "UNAVAILABLE", "ERROR"].includes(event.status as string)) throw new Error("事件內容不完整");
    if (event.researchOnly !== true) throw new Error("事件安全標記無效");
    ids.add(event.eventId);
    previousPhase = phaseIndex;
    previousSequence = event.phaseSequence as number;
    return event as DiscussionEvent;
  });
}

function responseState(status: number, events: DiscussionEvent[]): OrchestrationState {
  if (status === 429) return "rate_limited";
  if (status >= 500 || status === 404) return "unavailable";
  if (events.some((event) => event.status === "RATE_LIMITED")) return "rate_limited";
  if (events.some((event) => event.status === "ERROR")) return "partial";
  if (events.some((event) => event.status === "UNAVAILABLE")) return "partial";
  return "complete";
}

export async function fetchDiscussion(request: DiscussionRequest, signal?: AbortSignal): Promise<StudioOrchestration> {
  let response: Response;
  try {
    const endpoint = orchestrationEndpoint();
    if (!endpoint) {
      return {
        state: "unavailable",
        events: [],
        request,
        error: "公開作品未連接私人 AI 服務，請使用 DEMO 劇本。",
        source: null,
      };
    }
    response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify(request),
      signal,
    });
  } catch {
    return { state: "unavailable", events: [], request, error: "目前沒有可用的 AI 討論服務。", source: null };
  }
  if (response.status === 429) return { state: "rate_limited", events: [], request, error: "AI 討論服務目前忙碌，請稍後再試。", source: null };
  if (!response.ok) return { state: response.status >= 500 || response.status === 404 ? "unavailable" : "error", events: [], request, error: "AI 討論服務暫時無法使用。", source: null };
  try {
    const events = validateDiscussionEvents(rawEvents(await response.json()), request.sessionId);
    return { state: responseState(response.status, events), events, request, error: null, source: request.mode === "LIVE" ? "LIVE" : "MOCK" };
  } catch {
    return { state: "error", events: [], request, error: "收到的討論事件不符合前端契約。", source: null };
  }
}

export function demoOrchestration(scenario: DemoScenario): StudioOrchestration {
  return { state: "complete", events: demoEvents(scenario), request: requestForScenario(scenario, scenario.title, "DEMO"), error: null, source: "DEMO" };
}
