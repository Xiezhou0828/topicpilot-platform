import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("commercial navigation exposes only supported read-only surfaces", async () => {
  const foundation = await read("components/v2/V2Foundation.tsx");
  const primaryNav = foundation.slice(foundation.indexOf("export const navItems"), foundation.indexOf("export function Surface"));
  assert.match(primaryNav, /今日市場/);
  assert.match(primaryNav, /\/topics/);
  assert.match(primaryNav, /\/stocks/);
  assert.match(primaryNav, /\/favorites/);
  assert.doesNotMatch(primaryNav, /opportunities|ai-studio/);
  assert.match(foundation, /aria-current=\{currentPath === href \? "page"/);
  assert.doesNotMatch(foundation.match(/export function PrimaryNav[\s\S]*?\n\}/)?.[0] ?? "", /GlobalSearchShell|NotificationPlaceholder|AccountMenu/);
});

test("unfinished commercial routes fail closed and offer a supported return path", async () => {
  const page = await read("components/v2/V2Page.tsx");
  assert.match(page, /機會功能尚未發布/);
  assert.match(page, /沒有正式 Opportunity provider/);
  assert.match(page, /AI 研究室尚未發布/);
  assert.match(page, /沒有可供商用的 AI Research publication/);
  assert.match(page, /href="\/"/);
});

test("topic members link to exact market-aware Stock routes", async () => {
  const catalog = await read("components/v2/TopicCatalogPage.tsx");
  assert.match(catalog, /\/stocks\/\$\{encodeURIComponent\(member\.code\)\}/);
  assert.match(catalog, /new URLSearchParams\(\{ market: member\.market \}\)/);
  assert.match(catalog, /resource\.state === "ERROR" && <Button onClick=\{retry\}>重試<\/Button>/);
});

test("stock detail has a semantic list link and a direct-entry fallback", async () => {
  const detail = await read("stocks/[code]/page.tsx");
  assert.match(detail, /router\.push\("\/stocks"\)/);
  assert.match(detail, /<Link href="\/stocks">返回股票一覽<\/Link>/);
  assert.match(detail, /window\.history\.length > 1/);
  assert.match(detail, /router\.back/);
});

test("commercial surfaces define narrow viewport navigation and overflow containment", async () => {
  const css = await read("globals.css");
  assert.match(css, /@media\(max-width:760px\).*\.tp-nav-links\{width:100%;gap:4px;overflow-x:auto\}/s);
  assert.match(css, /\.tp-table-wrap\{max-width:100%;overflow-x:auto\}/);
  assert.match(css, /height:100dvh/);
  assert.match(css, /prefers-reduced-motion/);
});

test("retained legacy pages disclose their boundary and no legacy nav promotes them", async () => {
  const [nav, watchlist, studio, guide] = await Promise.all([
    read("components/AppNav.tsx"), read("watchlist/page.tsx"), read("studio/page.tsx"), read("guide/page.tsx"),
  ]);
  assert.doesNotMatch(nav, /href: "\/watchlist"|href: "\/studio"/);
  assert.match(nav, /href: "\/stocks"/);
  assert.match(watchlist, /Legacy Preview：此頁不是正式商用股票路徑/);
  assert.match(studio, /Legacy DEMO：此頁不是正式商用 AI 研究功能/);
  assert.doesNotMatch(guide, /href="\/watchlist"/);
});
