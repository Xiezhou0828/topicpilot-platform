import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  FAVORITES_STORAGE_KEY,
  buildFavoriteEntries,
  filterFavoriteEntries,
  groupFavoriteEntries,
  normalizeFavoriteCodes,
} from "../app/lib/favorites-view.mjs";

const stock = (code, name, parentGroup, topic) => ({
  code,
  name,
  relations: parentGroup || topic ? [{ parentGroup, topic }] : [],
  topicNames: topic ? [topic] : [],
});

test("existing local favorite format is preserved and normalized without a second key", () => {
  assert.equal(FAVORITES_STORAGE_KEY, "topic-pilot-favorites");
  assert.deepEqual(normalizeFavoriteCodes(["DEMO-A1", " DEMO-B2 ", "DEMO-A1", "", null]), ["DEMO-A1", "DEMO-B2"]);
});

test("favorite entries preserve local order and retain stocks missing from snapshot", () => {
  const entries = buildFavoriteEntries(
    ["DEMO-B2", "DEMO-X9", "DEMO-A1"],
    [stock("DEMO-A1", "Aster Systems", "Digital Infrastructure", "Edge AI"), stock("DEMO-B2", "Boreal Energy", "Sustainable Systems", "Clean Energy")],
    true,
  );
  assert.deepEqual(entries.map((entry) => entry.code), ["DEMO-B2", "DEMO-X9", "DEMO-A1"]);
  assert.equal(entries[1].status, "missing-stock");
  assert.equal(entries[1].stock, null);
  assert.equal(entries[1].mainGroup, "待分類");
});

test("snapshot unavailable differs from an individual missing stock", () => {
  const entries = buildFavoriteEntries(["DEMO-A1", "DEMO-X9"], [stock("DEMO-A1", "Aster Systems", "Digital Infrastructure", "Edge AI")], false);
  assert.deepEqual(entries.map((entry) => entry.status), ["snapshot-unavailable", "snapshot-unavailable"]);
  assert.equal(entries[0].stock.name, "Aster Systems");
  assert.equal(entries[1].stock, null);
});

test("group view uses formal parent group then fine topic and keeps unclassified separate", () => {
  const entries = buildFavoriteEntries(
    ["DEMO-A1", "DEMO-B2", "DEMO-X9"],
    [stock("DEMO-A1", "Aster Systems", "Digital Infrastructure", "Edge AI"), stock("DEMO-B2", "Boreal Energy", "Sustainable Systems", "Clean Energy")],
    true,
  );
  const groups = groupFavoriteEntries(entries);
  assert.deepEqual(groups.map((group) => group.name), ["Digital Infrastructure", "Sustainable Systems", "待分類"]);
  assert.equal(groups[0].topics[0].name, "Edge AI");
  assert.equal(groups[2].topics[0].name, "待分類");
});

test("search matches code, name, main group and topic without changing order", () => {
  const entries = buildFavoriteEntries(
    ["DEMO-B2", "DEMO-A1"],
    [stock("DEMO-A1", "Aster Systems", "Digital Infrastructure", "Edge AI"), stock("DEMO-B2", "Boreal Energy", "Sustainable Systems", "Clean Energy")],
    true,
  );
  assert.deepEqual(filterFavoriteEntries(entries, "DEMO-A1").map((entry) => entry.code), ["DEMO-A1"]);
  assert.deepEqual(filterFavoriteEntries(entries, "Energy").map((entry) => entry.code), ["DEMO-B2"]);
});

test("favorites route, navigation and shared change event are wired", () => {
  const nav = readFileSync(new URL("../app/components/AppNav.tsx", import.meta.url), "utf8");
  const button = readFileSync(new URL("../app/components/FavoriteButton.tsx", import.meta.url), "utf8");
  const page = readFileSync(new URL("../app/favorites/page.tsx", import.meta.url), "utf8");
  assert.match(nav, /href: "\/favorites", label: "我的觀察"/);
  assert.match(button, /topic-pilot-favorites-changed/);
  assert.match(button, /window\.addEventListener\("storage"/);
  assert.match(page, /自選資料僅保存在目前裝置/);
  assert.match(page, /目前資料不存在/);
  assert.match(page, /不代表系統推薦、持有或買進/);
  assert.match(page, /role=\{stock && !unavailable \? "link"/);
  assert.match(page, /event\.stopPropagation\(\)/);
});
