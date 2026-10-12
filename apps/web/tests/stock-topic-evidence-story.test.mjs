import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");
const [, storyComponent, detail, css, fixture1303, fixture1314, fixture1319] = await Promise.all([
  read("app/lib/stock-topic-evidence-preview.ts"),
  read("app/components/v2/StockTopicEvidenceStory.tsx"),
  read("app/components/v2/StockDetailPage.tsx"),
  read("app/globals.css"),
  read("app/data/topic-stories-v1/1303.json"),
  read("app/data/topic-stories-v1/1314.json"),
  read("app/data/topic-stories-v1/1319.json"),
]);

const storyCollections = [JSON.parse(fixture1303), JSON.parse(fixture1314), JSON.parse(fixture1319)];

test("formal Topic stories are authority-scoped and exclude emerging candidates", () => {
  assert.deepEqual(storyCollections.map((item) => item.stories.length), [3, 3, 3]);
  assert.deepEqual(storyCollections[0].stories.map((item) => item.canonicalTopicName), ["化工原料／塑化報價", "銅箔基板CCL", "玻纖布"]);
  assert.deepEqual(storyCollections[1].stories.map((item) => item.canonicalTopicName), ["化工原料／塑化報價", "住宅營建", "商辦／都市更新"]);
  assert.deepEqual(storyCollections[2].stories.map((item) => item.canonicalTopicName), ["電動車／EV", "其他車用電子", "ADAS"]);
  assert.doesNotMatch(fixture1303, /AI PCB/);
  assert.match(fixture1314, /formalTopicMutation": "NO/);
  assert.match(fixture1319, /formalTopicMutation": "NO/);
  for (const collection of storyCollections) {
    assert.equal(collection.schemaVersion, "stock-topic-evidence-collection.v1");
    for (const story of collection.stories) {
      assert.equal(story.schemaVersion, "stock-topic-evidence-view.v1");
      assert.match(story.formalAuthorityVersion, /topic-authority-lifecycle-formal-scope/);
      assert.match(story.structuralRoleReference.authorityVersion, /structural-role-authority/);
      assert.ok(story.nodes.length > 0);
      assert.ok(story.evidence.length > 0);
      for (const edge of story.edges) {
        assert.ok(story.nodes.some((node) => node.nodeId === edge.sourceNodeId));
        assert.ok(story.nodes.some((node) => node.nodeId === edge.targetNodeId));
        assert.ok(edge.evidenceRefs.every((id) => story.evidence.some((item) => item.evidenceId === id)));
      }
    }
  }
});

test("renderer is shared, pattern-driven, interactive and not stock hard-coded", () => {
  for (const marker of ["TopicStorySelector", "TopicStoryHeader", "TopicStoryRenderer", "EvidencePanel", "FinancialEvidence", "WatchIndicators", "ResearchLimitations", "EmergingResearchObservations", "onNode", "onEdge", "onEvidence"]) {
    assert.match(storyComponent, new RegExp(marker.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")));
  }
  assert.match(storyComponent, /ASSET_PROJECT_TIMELINE/);
  assert.match(storyComponent, /EVIDENCE_GAP/);
  assert.match(storyComponent, /sourceUrl/);
  assert.doesNotMatch(storyComponent, /stockId\s*===/);
  assert.doesNotMatch(storyComponent, /canonicalTopicName\s*===/);
  assert.match(detail, /StockTopicEvidenceStory (?:key=\{code\} )?collection=\{topicStoryCollection\}/);
  assert.match(detail, /getPreviewStockTopicStories/);
});

test("topic story layout keeps 60/40 desktop evidence reading and responsive fallback", () => {
  assert.match(css, /tp-topic-story-main-grid\{display:grid;grid-template-columns:minmax\(0,3fr\) minmax\(300px,2fr\)/);
  assert.match(css, /tp-topic-story-evidence-panel\{position:sticky/);
  assert.match(css, /@media\(max-width:980px\)\{\.tp-topic-story-header/);
  assert.match(css, /@media\(max-width:680px\)\{\.tp-topic-story-section/);
  assert.match(css, /tp-topic-story-selector button\.is-active/);
});

test("v2 renderer keeps node-edge integrity and readable data boundaries", () => {
  assert.match(storyComponent, /sourceNodeId/);
  assert.match(storyComponent, /targetNodeId/);
  assert.match(storyComponent, /selectedNode/);
  assert.match(storyComponent, /selectedEdge/);
  assert.match(storyComponent, /目前沒有支持此推論的可展示引用/);
  assert.match(storyComponent, /相關產品收入參考/);
  assert.match(storyComponent, /TWD_100_MILLION/);
  assert.match(storyComponent, /safePublicUrl/);
  assert.doesNotMatch(storyComponent, /index < story\.nodes\.length - 1/);
  assert.match(storyComponent, /不自動等同供貨、交易或獲利因果/);
});
