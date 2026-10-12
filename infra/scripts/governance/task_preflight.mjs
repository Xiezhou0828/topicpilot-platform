#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";

function parseArgs(argv) {
  const result = { peer: [], writeSet: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const value = argv[index + 1];
    if (value === undefined || value.startsWith("--")) {
      result[key] = true;
      continue;
    }
    index += 1;
    if (key === "peer" || key === "write-set") result[key === "peer" ? "peer" : "writeSet"].push(value);
    else result[key] = value;
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

function changedPaths(repo) {
  const output = git(repo, ["status", "--porcelain=v1"]);
  return output
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => line.slice(3).trim().replace(/^"|"$/g, ""));
}

function peerConflicts(repo, writeSet, peers) {
  if (!writeSet.length || !peers.length) return [];
  const conflicts = [];
  for (const peer of peers) {
    const peerPaths = new Set(changedPaths(peer));
    for (const path of writeSet) {
      if (peerPaths.has(path)) conflicts.push({ peer, path });
    }
  }
  return conflicts;
}

const args = parseArgs(process.argv.slice(2));
try {
  const repo = required(args, "repo");
  const taskId = required(args, "task-id");
  const branch = git(repo, ["branch", "--show-current"]);
  const head = git(repo, ["rev-parse", "HEAD"]);
  const commonDir = git(repo, ["rev-parse", "--git-common-dir"]);
  const remote = (() => {
    try { return git(repo, ["remote", "get-url", "origin"]); } catch { return null; }
  })();
  const dirtyPaths = changedPaths(repo);
  const detached = branch.length === 0;
  const preservationPath = args["preservation-manifest"] ? String(args["preservation-manifest"]) : null;
  const preservationVerified = preservationPath ? existsSync(preservationPath) : false;
  const conflicts = peerConflicts(repo, args.writeSet, args.peer);
  const checks = {
    branch: !detached && branch.startsWith("codex/"),
    clean: dirtyPaths.length === 0,
    commonDirectory: commonDir.length > 0,
    remote: Boolean(remote),
    preservation: preservationPath ? preservationVerified : false,
    sharedFiles: conflicts.length === 0,
  };
  const safeToStart = Object.values(checks).every(Boolean);
  const receipt = {
    taskId,
    repo,
    head,
    branch: branch || null,
    detached,
    commonDir,
    remote,
    dirtyPaths,
    preservationManifest: preservationPath,
    preservationVerified,
    sharedFileConflicts: conflicts,
    checks,
    safeToStart,
    disposition: safeToStart ? "PREFLIGHT_PASS" : "PREFLIGHT_FAIL_CLOSED",
  };
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
  process.exitCode = safeToStart ? 0 : 2;
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 64;
}
