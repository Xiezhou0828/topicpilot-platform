#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const value = argv[index + 1];
    if (value === undefined || value.startsWith("--")) result[key] = true;
    else { result[key] = value; index += 1; }
  }
  return result;
}

function required(args, key) {
  if (!args[key] || args[key] === true) throw new Error(`Missing --${key}`);
  return String(args[key]);
}

function git(repo, args) {
  return execFileSync("git", ["-C", repo, ...args], { encoding: "utf8" }).trim();
}

function existsAndPass(path) {
  if (!path || !existsSync(path)) return false;
  return /(?:STATUS|CHECK|VALIDATION|TEST|SCAN|PRESERVATION)[^\n]*(?:PASS|OK|VERIFIED)|(?:PASS|OK|VERIFIED)[^\n]*/i.test(readFileSync(path, "utf8"));
}

const args = parseArgs(process.argv.slice(2));
try {
  const repo = required(args, "repo");
  const taskId = required(args, "task-id");
  const branch = git(repo, ["branch", "--show-current"]);
  const head = git(repo, ["rev-parse", "HEAD"]);
  const dirty = git(repo, ["status", "--porcelain"]).length > 0;
  const sourceSha = args["source-sha"] ? String(args["source-sha"]) : null;
  const checks = {
    branch: branch.startsWith("codex/"),
    clean: !dirty,
    sourceInventory: existsAndPass(args["source-inventory"] ? String(args["source-inventory"]) : null),
    preservation: existsAndPass(args["preservation-manifest"] ? String(args["preservation-manifest"]) : null),
    validation: existsAndPass(args["validation-file"] ? String(args["validation-file"]) : null),
    secretsScan: existsAndPass(args["secrets-scan-file"] ? String(args["secrets-scan-file"]) : null),
    generatedArtifacts: existsAndPass(args["generated-check-file"] ? String(args["generated-check-file"]) : null),
    sourceMapping: existsAndPass(args["source-mapping"] ? String(args["source-mapping"]) : null),
    sourceMatchesHead: sourceSha ? sourceSha === head : false,
  };
  const deliveryReady = Object.values(checks).every(Boolean);
  const receipt = {
    taskId,
    gate: "DELIVERY_PREFLIGHT",
    repo,
    head,
    branch: branch || null,
    dirty,
    sourceSha,
    checks,
    deliveryReady,
    achievedState: deliveryReady ? "DELIVERY_READY" : "DELIVERY_BLOCKED",
    push: "NOT_EXECUTED",
    pr: "NOT_EXECUTED",
    merge: "NO",
    deploy: "NO",
    disposition: deliveryReady ? "DELIVERY_PREFLIGHT_PASS" : "DELIVERY_PREFLIGHT_FAIL_CLOSED",
  };
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
  process.exitCode = deliveryReady ? 0 : 2;
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 64;
}
