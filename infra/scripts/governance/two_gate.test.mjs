import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const root = new URL(".", import.meta.url).pathname.replace(/^\//, "").replaceAll("/", "\\");
const development = join(root, "development_preflight.mjs");
const delivery = join(root, "delivery_preflight.mjs");

function fixture() {
  const dir = mkdtempSync(join(tmpdir(), "topicpilot-two-gate-"));
  execFileSync("git", ["init", "-b", "codex/two-gate", dir], { stdio: "ignore" });
  execFileSync("git", ["-C", dir, "config", "user.email", "test@example.invalid"]);
  execFileSync("git", ["-C", dir, "config", "user.name", "Test"]);
  execFileSync("git", ["-C", dir, "remote", "add", "origin", "https://example.invalid/topicpilot.git"]);
  writeFileSync(join(dir, "README.md"), "fixture\n");
  execFileSync("git", ["-C", dir, "add", "README.md"]);
  execFileSync("git", ["-C", dir, "commit", "-m", "fixture"], { stdio: "ignore" });
  return dir;
}

test("development gate permits dirty work while delivery gate blocks it", () => {
  const dir = fixture();
  writeFileSync(join(dir, "dirty.txt"), "local iteration\n");
  const developmentResult = spawnSync(process.execPath, [
    development, "--repo", dir, "--task-id", "TEST", "--preview-origin", "http://127.0.0.1:4318",
    "--financial-api-origin", "http://127.0.0.1:8001", "--research-read-model-mode", "NOT_CONNECTED",
  ], { encoding: "utf8" });
  assert.equal(developmentResult.status, 0, developmentResult.stderr);
  assert.match(developmentResult.stdout, /LOCAL_DEV_DIRTY/);

  const deliveryResult = spawnSync(process.execPath, [
    delivery, "--repo", dir, "--task-id", "TEST", "--source-sha", execFileSync("git", ["-C", dir, "rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
    "--source-inventory", join(dir, "missing"), "--preservation-manifest", join(dir, "missing"),
    "--validation-file", join(dir, "missing"), "--secrets-scan-file", join(dir, "missing"),
    "--generated-check-file", join(dir, "missing"), "--source-mapping", join(dir, "missing"),
  ], { encoding: "utf8" });
  assert.equal(deliveryResult.status, 2);
  assert.match(deliveryResult.stdout, /DELIVERY_BLOCKED/);
});
