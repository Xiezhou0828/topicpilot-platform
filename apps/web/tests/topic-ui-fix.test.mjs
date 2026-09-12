import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Topic group accordions keep closed cards from stretching in the same grid row", async () => {
  const [page, css] = await Promise.all([
    read("components/v2/TopicListPage.tsx"),
    read("globals.css"),
  ]);
  assert.match(page, /tp-topic-group-grid/);
  assert.match(page, /openGroups/);
  assert.match(page, /tp-topic-group-card \$\{isOpen \? "is-open" : ""\}/);

  const rule = css.match(/\.tp-topic-group-grid\{([^}]*)\}/)?.[1];
  assert.ok(rule, "Topic group grid rule should remain present");
  assert.match(css, /\/\* Topic group accordions must size independently within a shared grid row\. \*\//);
  assert.match(css, /\.tp-topic-group-grid\{align-items:start\}/);
  assert.doesNotMatch(rule, /align-items:stretch/);
});
