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
  assert.match(page, /tp-topic-v1-parent-nav/);
  assert.match(page, /selectedParent/);
  assert.match(page, /tp-topic-v1-parent-nav/);

  assert.match(css, /\.tp-topic-v1-parent-nav\{/);
  assert.match(css, /grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
});
