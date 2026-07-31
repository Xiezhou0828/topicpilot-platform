import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

let workerPromise;

async function getWorker() {
  workerPromise ??= import(new URL("../dist/server/index.js", import.meta.url).href).then((module) => module.default);
  return workerPromise;
}

async function render(pathname) {
  const worker = await getWorker();
  return worker.fetch(
    new Request(`http://localhost${pathname}`, { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

const routeCases = [
  ["/", "把市場資料"],
  ["/stocks", "股票宇宙"],
  ["/stocks/SYN-101", "正在讀取個股資料輪廓"],
  ["/topics", "題材輪動"],
  ["/topics/edge-computing", "正在展開題材資料"],
  ["/strategies", "策略實驗室"],
  ["/data-status", "資料狀態與系統架構"],
  ["/architecture", "資料狀態與系統架構"],
];

for (const [pathname, expectedCopy] of routeCases) {
  test(`server-renders product route ${pathname}`, async () => {
    const response = await render(pathname);
    assert.equal(response.status, 200);
    assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
    const html = await response.text();
    assert.match(html, new RegExp(expectedCopy));
    assert.match(html, /展示資料・非投資建議/);
    assert.match(html, /TopicPilot/);
    assert.doesNotMatch(html, /codex-preview|Building your site|react-loading-skeleton/i);
  });
}

test("starter preview assets and dependency are removed", async () => {
  const packageJson = await readFile(new URL("../package.json", import.meta.url), "utf8");
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await assert.rejects(readFile(new URL("../app/_sites-preview/SkeletonPreview.tsx", import.meta.url)));
  assert.match(packageJson, /cross-env/);
});

test("hosting declaration remains stateless", async () => {
  const hosting = JSON.parse(await readFile(new URL("../.openai/hosting.json", import.meta.url), "utf8"));
  assert.deepEqual(hosting, { d1: null, r2: null });
});
