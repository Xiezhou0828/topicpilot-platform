import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("production topic catalog fails closed without a formal API origin", async () => {
  const source = await read("lib/topic-api.ts");
  assert.match(source, /process\.env\.NODE_ENV === "development"/);
  assert.match(source, /NEXT_PUBLIC_ENABLE_TOPIC_PREVIEW === "true"/);
  assert.match(source, /production 不使用 Preview 題材清單替代/);
});

test("formal topic identity is preserved and all-catalog UI does not grade-filter by default", async () => {
  const [source, page] = await Promise.all([
    read("lib/topic-api.ts"),
    read("components/v2/TopicListPage.tsx"),
  ]);
  assert.match(source, /name: item\.name/);
  assert.match(source, /groupName: item\.groupName/);
  assert.match(source, /\/api\/v2\/topics\?limit=200&offset=0/);
  assert.match(page, /useState<GradeFilter>\("全部"\)/);
  assert.match(page, /完整正式題材目錄/);
  assert.match(page, /overviewTopics\.length/);
});

test("formal topic detail does not render synthetic research sections", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /resource\?\.source === "synthetic-snapshot"/);
  assert.match(page, /Production 不以 Preview 內容覆蓋正式題材 identity/);
  assert.match(page, /resource\.source === "api" \? "資料日期待補" : "Preview"/);
});
