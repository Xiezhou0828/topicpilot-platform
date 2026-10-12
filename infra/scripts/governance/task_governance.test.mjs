import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const root = new URL(".", import.meta.url).pathname.replace(/^\//, "").replaceAll("/", "\\");
const preflight = join(root, "task_preflight.mjs");
const delivery = join(root, "task_delivery_check.mjs");

function fixture() {
  const dir = mkdtempSync(join(tmpdir(), "topicpilot-governance-"));
  execFileSync("git", ["init", "-b", "codex/test-governance", dir], { stdio: "ignore" });
  execFileSync("git", ["-C", dir, "config", "user.email", "test@example.invalid"]);
  execFileSync("git", ["-C", dir, "config", "user.name", "Test"]);
  execFileSync("git", ["-C", dir, "remote", "add", "origin", "https://example.invalid/topicpilot.git"]);
  writeFileSync(join(dir, "README.md"), "fixture\n");
  execFileSync("git", ["-C", dir, "add", "README.md"]);
  execFileSync("git", ["-C", dir, "commit", "-m", "fixture"], { stdio: "ignore" });
  const preservationDir = mkdtempSync(join(tmpdir(), "topicpilot-preservation-"));
  const preservation = join(preservationDir, "PRESERVATION_VERIFIED");
  writeFileSync(preservation, "PRESERVATION_VERIFIED\n");
  return { dir, preservation };
}

test("governance gates cover clean, dirty, and delivery states", () => {
  const clean = fixture();
  const cleanResult = spawnSync(process.execPath, [preflight, "--repo", clean.dir, "--task-id", "TEST", "--preservation-manifest", clean.preservation], { encoding: "utf8" });
  assert.equal(cleanResult.status, 0, cleanResult.stderr);
  assert.match(cleanResult.stdout, /PREFLIGHT_PASS/);

  const dirty = fixture();
  writeFileSync(join(dirty.dir, "dirty.txt"), "dirty\n");
  const dirtyResult = spawnSync(process.execPath, [preflight, "--repo", dirty.dir, "--task-id", "TEST", "--preservation-manifest", dirty.preservation], { encoding: "utf8" });
  assert.equal(dirtyResult.status, 2);
  assert.match(dirtyResult.stdout, /PREFLIGHT_FAIL_CLOSED/);
  assert.match(dirtyResult.stdout, /dirty\.txt/);

  const { dir, preservation } = fixture();
  const report = join(dir, "validation.md");
  writeFileSync(report, "VALIDATION_STATUS=PASS\n");
  const result = spawnSync(process.execPath, [delivery, "--repo", dir, "--task-id", "TEST", "--required-terminal-state", "CANONICALIZED", "--validation-file", report, "--preservation-manifest", preservation, "--source-sha", execFileSync("git", ["-C", dir, "rev-parse", "HEAD"], { encoding: "utf8" }).trim()], { encoding: "utf8" });
  assert.equal(result.status, 2);
  assert.match(result.stdout, /"deliveryState": "VALIDATED"/);
  assert.match(result.stdout, /"taskComplete": false/);
});
