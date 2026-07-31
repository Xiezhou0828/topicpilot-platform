import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import {
  assignmentForCharacter,
  panelAfterCharacterSelect,
  performanceIdentity,
  selectCustomTopic,
} from "../app/studio/studio-state.mjs";

test("character assignment lookup never carries another character model", () => {
  const assignments = [
    { characterId: "coda", modelId: "codex-demo", strategyId: "rule-momentum" },
    { characterId: "mori", modelId: "claude-demo", strategyId: "risk-pullback" },
  ];
  assert.equal(assignmentForCharacter(assignments, "coda").modelId, "codex-demo");
  assert.equal(assignmentForCharacter(assignments, "mori").strategyId, "risk-pullback");
  assert.equal(assignmentForCharacter(assignments, "volt"), null);
});

test("performance identity includes model, strategy and session versions", () => {
  assert.equal(
    performanceIdentity("model-v1", "strategy-v2", "session-v3"),
    "model-v1::strategy-v2::session-v3",
  );
});

test("custom topic waits for API and does not fabricate an answer", () => {
  assert.deepEqual(selectCustomTopic("  大盤量縮反彈  "), {
    topic: "大盤量縮反彈",
    state: "WAITING_API",
    message: "等待模型 API；不會產生模擬回答。",
  });
  assert.equal(selectCustomTopic(" ").state, "EMPTY");
});

test("clicking a room character opens that character panel", () => {
  assert.deepEqual(panelAfterCharacterSelect("prism"), { characterId: "prism", tab: "character" });
});

test("studio source exposes four fixed characters, demo safety and accessible controls", async () => {
  const [page, fixture, types, css, layout] = await Promise.all([
    readFile(new URL("../app/studio/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/studio/studio-fixture.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/studio/studio-types.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  ]);
  for (const name of ["Coda", "Mori", "Prism", "Volt"]) assert.match(fixture, new RegExp(name));
  for (const scenario of ["數位基礎設施轉強", "雲端服務高檔分歧", "大盤開高走低"]) assert.match(fixture, new RegExp(scenario));
  for (const typeName of ["CharacterProfile", "ModelProfile", "StrategyProfile", "AgentAssignment", "StudioSession", "StudioOpinion", "PortfolioSnapshot"]) {
    assert.match(types, new RegExp("type " + typeName));
  }
  assert.match(page, /非模型即時生成／非真實投資績效/);
  assert.match(page, /等待模型 API/);
  assert.match(page, /aria-label=.*查看/);
  assert.match(page, /role="tab"/);
  assert.doesNotMatch(page, /aiTraders|studioMessages/);
  assert.doesNotMatch(fixture, /fetch\(|process\.env|API_KEY/);
  assert.match(css, /@media \(max-width: 900px\)/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /image-rendering: pixelated/);
  assert.match(page, /height=\{844\}[^>]+studio-room-v2\.png/);
  assert.match(css, /aspect-ratio: 1008 \/ 844/);
  assert.match(css, /grid-template-columns: minmax\(0, 1fr\)/);
  assert.match(css, /\.pixelStudioShell \{[^}]*overflow-x: hidden/s);
  assert.doesNotMatch(css, /\.pixelRoom \{[^}]*max-height/s);
  assert.match(page, /loading="eager"[^>]+unoptimized/);
  assert.match(page, /roomCharacterSprite/);
  assert.match(page, /roomOcclusionTable/);
  assert.match(page, /roomCharacterStatus/);
  assert.match(css, /@keyframes codaIdle/);
  assert.match(css, /@keyframes studioScanline/);
  assert.match(css, /\.crtOverlay \{[^}]*background: transparent/s);
  assert.match(css, /\.roomCharacterHotspot\.selected \{[\s\S]*?border-color: transparent/);
  assert.doesNotMatch(page, /roomCharacterShadow/);
  assert.match(layout, /width: "device-width"/);
});
