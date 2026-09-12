import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("frontend freezes the Owner five-stage order and availability boundary", async () => {
  const contract = await read("lib/topic-lifecycle-contract.ts");
  assert.match(contract, /OWNER_LIFECYCLE_STAGES = \["萌芽", "發酵", "主升", "成熟", "衰退"\]/);
  assert.match(contract, /WAITING_FOR_FORMAL_LINEAGE/);
  assert.match(contract, /高檔整理.*成熟/);
  assert.match(contract, /退潮.*衰退/);
  assert.doesNotMatch(contract, /資料待累積.*OWNER_LIFECYCLE_STAGES/);
});

test("formal frontend mapping uses backend enums and does not promote legacy aliases", async () => {
  const [contract, overview, detail] = await Promise.all([
    read("lib/topic-lifecycle-contract.ts"),
    read("components/v2/TopicListPage.tsx"),
    read("components/v2/TopicDetailPage.tsx"),
  ]);
  assert.match(contract, /ownerStageFromBackend/);
  assert.match(overview, /return ownerStageFromBackend\(stage\)/);
  assert.match(detail, /return ownerStageFromBackend\(stage\)/);
  assert.doesNotMatch(overview, /MATURE:\s*"高檔整理"/);
  assert.doesNotMatch(detail, /DECLINING:\s*"退潮"/);
});

test("generated API declaration carries the lifecycle availability and lineage additions", async () => {
  const generated = await read("lib/generated-api.d.ts");
  assert.match(generated, /WAITING_FOR_FORMAL_LINEAGE/);
  assert.match(generated, /\/\*\* Lineage \*\//);
});
