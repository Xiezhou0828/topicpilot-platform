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

const args = parseArgs(process.argv.slice(2));
try {
  const repo = required(args, "repo");
  const taskId = required(args, "task-id");
  const requiredTerminalState = required(args, "required-terminal-state");
  const branch = git(repo, ["branch", "--show-current"]);
  const head = git(repo, ["rev-parse", "HEAD"]);
  const dirty = git(repo, ["status", "--porcelain"]).length > 0;
  const validationFile = args["validation-file"] ? String(args["validation-file"]) : null;
  const validationText = validationFile && existsSync(validationFile) ? readFileSync(validationFile, "utf8") : "";
  const validationPass = /(?:VALIDATION|TEST|STATUS)[^\n]*PASS|PASS[^\n]*/i.test(validationText);
  const preservationFile = args["preservation-manifest"] ? String(args["preservation-manifest"]) : null;
  const preservationVerified = Boolean(preservationFile && existsSync(preservationFile));
  const sourceSha = args["source-sha"] ? String(args["source-sha"]) : null;
  const sourceMatchesHead = sourceSha ? sourceSha === head : false;
  const taskBranch = branch.startsWith("codex/");
  const committedLocal = taskBranch && !dirty && sourceMatchesHead;
  const canonicalized = args["canonical-sha"] === head && args["canonical-status"] === "PASS";
  const currentState = canonicalized ? "CANONICALIZED" : committedLocal ? "COMMITTED_LOCAL" : validationPass && preservationVerified ? "VALIDATED" : "IMPLEMENTED_LOCAL";
  const nextRequired = canonicalized ? "OWNER_RELEASE_GATE" : committedLocal ? "CANONICAL_RECONCILIATION" : "TASK_BRANCH_COMMIT_AND_VALIDATION";
  const receipt = {
    taskId,
    repo,
    requiredTerminalState,
    achievedTerminalState: canonicalized ? "CANONICALIZED" : validationPass ? "VALIDATED" : "IMPLEMENTED",
    deliveryState: currentState,
    head,
    branch: branch || null,
    dirty,
    validationFile,
    validationPass,
    preservationVerified,
    sourceSha,
    sourceMatchesHead,
    canonicalized,
    push: "NOT_CHECKED_WITHOUT_EXPLICIT_REMOTE_RECEIPT",
    merge: "NO",
    deploy: "NO",
    nextRequired,
    taskComplete: canonicalized && requiredTerminalState === "CANONICALIZED",
  };
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
  process.exitCode = receipt.taskComplete ? 0 : 2;
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 64;
}
