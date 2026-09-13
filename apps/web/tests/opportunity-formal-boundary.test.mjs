import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);

test("Opportunity route is an explicit formal-provider boundary", async () => {
  const page = await readFile(new URL("components/v2/V2Page.tsx", app), "utf8");

  assert.match(page, /path === ".*opportunities/);
  assert.match(page, /機會功能尚未發布/);
  assert.match(page, /正式 Opportunity provider/);
  assert.match(page, /不會用前端篩選或示範資料產生機會清單/);
  assert.match(page, /state="UNAVAILABLE"/);
  assert.doesNotMatch(page, /shadow|fixture|mock|ranked|score|recommend/i);
});
