import type {
  CharacterProfile,
  DemoScenario,
  ModelProfile,
  PortfolioSnapshot,
  StrategyProfile,
} from "./studio-types";

export const characters: CharacterProfile[] = [
  {
    id: "coda", name: "Coda", color: "#5ad7d3", portrait: "/studio/coda-portrait.png", roomSprite: "/studio/coda-work.png", roomSpriteWidth: 486,
    visual: "藍綠小型人形機器人", personality: "冷靜、簡潔、規則導向",
    speakingStyle: "先列條件，再給可執行結論", meetingRole: "提出方案與驗證條件",
    strength: "把趨勢、動能、突破與量能整理成明確流程", blindSpot: "過度依賴規則時，可能低估事件造成的跳空",
    roomPosition: { left: "16%", top: "54%" },
  },
  {
    id: "mori", name: "Mori", color: "#f0b84f", portrait: "/studio/mori-portrait.png", roomSprite: "/studio/mori-work.png", roomSpriteWidth: 375,
    visual: "銀髮年長風控管家", personality: "謹慎、完整、擅長反駁",
    speakingStyle: "先問失效價，再談報酬空間", meetingRole: "提出風險與否決理由",
    strength: "支撐回測、流動性與部位風險", blindSpot: "容易因要求太完整而錯過快速主升段",
    roomPosition: { left: "15%", top: "79%" },
  },
  {
    id: "prism", name: "Prism", color: "#b888ff", portrait: "/studio/prism-portrait.png", roomSprite: "/studio/prism-work.png", roomSpriteWidth: 641,
    visual: "紫髮女性研究員", personality: "好奇、多角度、擅長比較",
    speakingStyle: "並列不同假設，檢查題材與籌碼是否共振", meetingRole: "負責輪動、廣度與籌碼",
    strength: "題材廣度、法人籌碼與相對強弱交叉比較", blindSpot: "資訊面向太多時，決策速度可能偏慢",
    roomPosition: { left: "84%", top: "53%" },
  },
  {
    id: "volt", name: "Volt", color: "#ff7b45", portrait: "/studio/volt-portrait.png", roomSprite: "/studio/volt-work.png", roomSpriteWidth: 503,
    visual: "橘髮年輕偵察員", personality: "直接、挑戰共識、反應快速",
    speakingStyle: "直接指出市場意外與擁擠交易", meetingRole: "負責事件、情緒與逆向機會",
    strength: "捕捉事件動能、情緒極端與短線錯價", blindSpot: "積極假設若缺少確認，容易承受較大波動",
    roomPosition: { left: "85%", top: "80%" },
  },
];

export const models: ModelProfile[] = [
  { id: "codex-demo", provider: "OpenAI", modelName: "Codex", modelVersion: "demo-model-v0", badge: "Codex", apiStatus: "UNAVAILABLE" },
  { id: "claude-demo", provider: "Anthropic", modelName: "Claude", modelVersion: "demo-model-v0", badge: "Claude", apiStatus: "UNAVAILABLE" },
  { id: "gemini-demo", provider: "Google", modelName: "Gemini", modelVersion: "demo-model-v0", badge: "Gemini", apiStatus: "UNAVAILABLE" },
  { id: "grok-demo", provider: "xAI", modelName: "Grok", modelVersion: "demo-model-v0", badge: "Grok", apiStatus: "UNAVAILABLE" },
];

export const strategies: StrategyProfile[] = [
  { id: "rule-momentum", name: "規則動能", strategyVersion: "strategy-coda-v1", factors: ["趨勢", "動能", "突破", "量能"], holdingPeriod: "2–10 個交易日", positionCount: "3–5 檔", riskPreference: "平衡" },
  { id: "risk-pullback", name: "風控回測", strategyVersion: "strategy-mori-v1", factors: ["支撐回測", "失效價", "流動性"], holdingPeriod: "3–15 個交易日", positionCount: "4–6 檔", riskPreference: "保守" },
  { id: "topic-breadth", name: "題材籌碼", strategyVersion: "strategy-prism-v1", factors: ["題材輪動", "法人籌碼", "族群廣度"], holdingPeriod: "3–20 個交易日", positionCount: "5–8 檔", riskPreference: "平衡分散" },
  { id: "event-contrarian", name: "事件逆向", strategyVersion: "strategy-volt-v1", factors: ["事件動能", "情緒極端", "逆向機會"], holdingPeriod: "1–5 個交易日", positionCount: "2–4 檔", riskPreference: "積極" },
];

const assignmentSeed = [
  ["coda", "codex-demo", "rule-momentum"],
  ["mori", "claude-demo", "risk-pullback"],
  ["prism", "gemini-demo", "topic-breadth"],
  ["volt", "grok-demo", "event-contrarian"],
] as const;

function scenario(
  id: string,
  title: string,
  shortLabel: string,
  summaries: [string, string, string, string],
  conclusion: string,
): DemoScenario {
  const sessionId = `demo-${id}`;
  const sessionVersion = `session-${id}-v1`;
  const stages = ["independent", "debate", "conclusion"] as const;
  return {
    id, title, shortLabel, conclusion,
    session: { id: sessionId, sessionVersion, title, mode: "DEMO", source: "SCRIPTED_FIXTURE", asOf: "盤後示範劇本" },
    assignments: assignmentSeed.map(([characterId, modelId, strategyId]) => ({
      id: `${sessionId}-${characterId}`, sessionId, characterId, modelId, strategyId,
    })),
    opinions: assignmentSeed.flatMap(([characterId], index) => stages.map((stage, stageIndex) => ({
      id: `${sessionId}-${stage}-${characterId}`, sessionId, stage, characterId,
      stance: (index === 1 ? "保守" : index === 2 ? "中性" : "看多") as "看多" | "中性" | "保守",
      confidence: Math.max(52, 82 - index * 6 - stageIndex * 2),
      summary: stage === "independent"
        ? summaries[index]
        : stage === "debate"
          ? ["量價確認後才執行，否則保留現金。", "同意題材，但不同意在風險報酬不足時追價。", "要看族群廣度，不接受只靠單一強股。", "市場共識太整齊時，反而要防隔日反轉。"][index]
          : ["只保留符合觸發與量能條件的候選。", "先寫失效條件，再決定部位。", "確認題材與籌碼共振後才提高權重。", "保留小倉位應對事件意外。"][index],
      reasons: [["趨勢與動能", "觸發條件"], ["支撐與失效", "流動性"], ["題材廣度", "法人籌碼"], ["事件強度", "市場情緒"]][index],
      risk: ["突破失敗", "開高走低", "族群分歧", "事件反轉"][index],
      invalidation: ["量能未確認", "跌破支撐", "廣度快速收斂", "消息未被價格承接"][index],
      candidates: [["Aster Systems", "Cipher Cloud"], ["Boreal Energy", "Delta Components"], ["Cipher Cloud", "Aster Systems"], ["Delta Components", "Boreal Energy"]][index],
      sealed: stage === "independent",
    }))),
  };
}

export const demoScenarios: DemoScenario[] = [
  scenario("infrastructure", "數位基礎設施轉強", "基礎設施轉強", [
    "合成族群同步站回短均線，等待放量突破。",
    "先排除融資升溫與失效價太遠的標的。",
    "題材廣度改善，但法人共振仍需確認。",
    "若市場只追單一龍頭，可能是短線擁擠。",
  ], "數位基礎設施列為主觀察；只接受量能確認、失效價明確的候選。"),
  scenario("cloud", "雲端服務高檔分歧", "雲端服務分歧", [
    "主流尚未結束，但只看低風險突破。",
    "高檔爆量與融資升溫標的優先降級。",
    "封測與模組出現輪動，廣度不再一致。",
    "市場過度樂觀時，隔日沖風險會被低估。",
  ], "不否定合成題材趨勢，但整體降至第二觀察並縮小部位。"),
  scenario("index", "大盤開高走低", "開高走低", [
    "強勢題材若守住早盤支撐，仍可個別觀察。",
    "大盤轉弱時停止追價，先保留現金。",
    "檢查題材廣度是否同步轉差，避免只看指數。",
    "若恐慌集中在尾盤，隔日可能出現情緒修復。",
  ], "風險開關轉為保守；只保留相對強勢與失效距離短的觀察股。"),
];

export const portfolioSnapshots: PortfolioSnapshot[] = [
  { id: "pf-coda", characterId: "coda", modelVersion: "demo-model-v0", strategyVersion: "strategy-coda-v1", sessionVersion: "session-infrastructure-v1", status: "DEMO", returnPct: 8.4, excessReturnPct: 3.1, winRate: 57, maxDrawdownPct: -3.2, sampleSize: 14, equity: [100, 101.2, 102.8, 101.9, 104.6, 106.2, 108.4], holdings: [{ code: "DEMO-A1", name: "Aster Systems", weight: 38, note: "等待量能確認" }] },
  { id: "pf-mori", characterId: "mori", modelVersion: "demo-model-v0", strategyVersion: "strategy-mori-v1", sessionVersion: "session-infrastructure-v1", status: "DEMO", returnPct: 4.1, excessReturnPct: 1.2, winRate: 63, maxDrawdownPct: -1.6, sampleSize: 16, equity: [100, 100.7, 101.4, 101.1, 102.6, 103.2, 104.1], holdings: [{ code: "DEMO-B2", name: "Boreal Energy", weight: 24, note: "只接受回測不破" }] },
  { id: "pf-prism", characterId: "prism", modelVersion: "demo-model-v0", strategyVersion: "strategy-prism-v1", sessionVersion: "session-infrastructure-v1", status: "DEMO", returnPct: 6.7, excessReturnPct: 2.4, winRate: 52, maxDrawdownPct: -2.7, sampleSize: 18, equity: [100, 99.6, 101.8, 103.1, 102.4, 105.9, 106.7], holdings: [{ code: "DEMO-C3", name: "Cipher Cloud", weight: 22, note: "題材關聯示範" }] },
  { id: "pf-volt", characterId: "volt", modelVersion: "demo-model-v0", strategyVersion: "strategy-volt-v1", sessionVersion: "session-infrastructure-v1", status: "DEMO", returnPct: 3.8, excessReturnPct: 0.9, winRate: 46, maxDrawdownPct: -4.5, sampleSize: 11, equity: [100, 102.1, 99.8, 103.4, 101.9, 105.2, 103.8], holdings: [{ code: "DEMO-D4", name: "Delta Components", weight: 18, note: "空值處理示範" }] },
];
