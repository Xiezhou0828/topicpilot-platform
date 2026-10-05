import { spawn } from "node:child_process";
import { promises as fs, readdirSync } from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

import { normalizeReadOnlyApiOrigin } from "./preview_proxy.mjs";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(SCRIPT_DIR, "../..");
const WEB_ROOT = path.join(REPO_ROOT, "apps", "web");
const PREVIEW_RECORD = path.join(WEB_ROOT, "public", "__preview.json");
const NODE = process.execPath;
const NPM = process.platform === "win32" ? "npm.cmd" : "npm";
const NPX = process.platform === "win32" ? "npx.cmd" : "npx";

function fail(message) {
  throw new Error(message);
}

function capture(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd ?? REPO_ROOT,
      env: options.env ?? process.env,
      stdio: ["ignore", "pipe", "pipe"],
      shell: process.platform === "win32" && command.endsWith(".cmd"),
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code, signal) => resolve({ code, signal, stdout, stderr }));
  });
}

async function run(command, args, options = {}) {
  const result = await new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd ?? REPO_ROOT,
      env: options.env ?? process.env,
      stdio: "inherit",
      shell: process.platform === "win32" && command.endsWith(".cmd"),
    });
    child.on("error", reject);
    child.on("close", (code, signal) => resolve({ code, signal }));
  });
  if (result.code !== 0) {
    fail(`${command} ${args.join(" ")} failed with ${result.code ?? result.signal}`);
  }
  return result;
}

async function gitOutput(args) {
  const result = await capture("git", args);
  if (result.code !== 0) fail(result.stderr.trim() || `git ${args.join(" ")} failed`);
  return result.stdout.trim();
}

export function parseReviewConfig(argv = process.argv.slice(2)) {
  const { values, positionals } = parseArgs({
    args: argv,
    allowPositionals: true,
    options: {
      mode: { type: "string", default: "iterative" },
      "candidate-ref": { type: "string" },
      "read-api-origin": { type: "string" },
      port: { type: "string", default: "3000" },
      "skip-install": { type: "boolean", default: false },
    },
  });
  if (positionals.length > 0) fail(`UNEXPECTED_ARGUMENT=${positionals[0]}`);

  const mode = values.mode === "exact-sha" ? "EXACT_SHA_CANDIDATE" : values.mode === "iterative" ? "ITERATIVE_LOCAL" : null;
  if (!mode) fail("MODE_MUST_BE_ITERATIVE_OR_EXACT_SHA");

  const port = Number(values.port);
  if (!Number.isInteger(port) || port < 1 || port > 65535) fail("PORT_MUST_BE_1_TO_65535");

  const readApiOrigin = values["read-api-origin"]
    ? normalizeReadOnlyApiOrigin(values["read-api-origin"])
    : null;
  if (mode === "EXACT_SHA_CANDIDATE" && !values["candidate-ref"]) {
    fail("EXACT_SHA_CANDIDATE_REQUIRES_CANDIDATE_REF");
  }

  return {
    mode,
    candidateRef: values["candidate-ref"] ?? null,
    readApiOrigin,
    port,
    skipInstall: values["skip-install"] === true,
    dataMode: readApiOrigin ? "REAL_READ_ONLY" : "REPRESENTATIVE_SYNTHETIC",
  };
}

export function assertExactReviewState({ candidateSha, headSha, status }) {
  if (headSha !== candidateSha) fail("EXACT_SHA_CHECKOUT_MISMATCH");
  if (status.trim()) fail("EXACT_SHA_REVIEW_REQUIRES_CLEAN_WORKTREE");
  return true;
}

function frontendTestFiles() {
  return readdirSync(path.join(WEB_ROOT, "tests"))
    .filter((name) => name.endsWith(".test.mjs"))
    .sort()
    .map((name) => path.join("tests", name));
}

function runtimeEnvironment(config) {
  const localOrigin = `http://localhost:${config.port}`;
  return {
    ...process.env,
    NEXT_PUBLIC_API_BASE_URL: config.readApiOrigin ? localOrigin : "",
    NEXT_PUBLIC_SNAPSHOT_API_URL: "",
    NEXT_PUBLIC_ENABLE_DEMO_FALLBACK: config.readApiOrigin ? "false" : "true",
    NEXT_PUBLIC_PREVIEW_MODE: "true",
    NEXT_PUBLIC_ENABLE_TOPIC_PREVIEW: "true",
    NEXT_PUBLIC_AI_STUDIO_ORCHESTRATION_URL: "",
    TOPICPILOT_PREVIEW_READ_API_ORIGIN: config.readApiOrigin ?? "",
  };
}

async function prepareExactCandidate(config, env) {
  const candidateSha = await gitOutput(["rev-parse", "--verify", `${config.candidateRef}^{commit}`]);
  const headSha = await gitOutput(["rev-parse", "HEAD"]);
  const status = await gitOutput(["status", "--porcelain=v1", "--untracked-files=all"]);
  assertExactReviewState({ candidateSha, headSha, status });

  if (!config.skipInstall) await run(NPM, ["ci", "--prefix", "apps/web"], { env });
  await run(NODE, ["--test", "infra/scripts/tests/preview_provenance.test.mjs"], { env });
  await run(NODE, ["--test", "apps/web/tests/topic-catalog-formal-integration.test.mjs"], { env });
  await run(NPM, ["run", "demo:snapshot:check", "--prefix", "apps/web"], { env });
  await run(NPM, ["run", "lint", "--prefix", "apps/web"], { env });
  await run(NPX, ["tsc", "--noEmit"], { cwd: WEB_ROOT, env });

  await run(NODE, [
    "infra/scripts/preview_provenance.mjs",
    "write",
    "--repo-root", REPO_ROOT,
    "--candidate-sha", candidateSha,
    "--candidate-ref", config.candidateRef,
    "--api-base-url", config.readApiOrigin ?? "",
    "--output", PREVIEW_RECORD,
  ], { env });
  await run(NPM, ["run", "build", "--prefix", "apps/web"], { env });
  await run(NODE, [
    "infra/scripts/preview_provenance.mjs",
    "verify",
    "--artifact-dir", path.join(WEB_ROOT, "dist"),
    "--candidate-sha", candidateSha,
  ], { env });
  await run(NODE, ["--test", ...frontendTestFiles()], { cwd: WEB_ROOT, env });
  return candidateSha;
}

async function waitForUrl(url, child, timeoutMs = 180_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = "not yet reachable";
  while (Date.now() < deadline) {
    if (child.exitCode !== null) fail(`PREVIEW_SERVER_EXITED=${child.exitCode}`);
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(15_000) });
      if (response.ok) return response;
      lastError = `HTTP_${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  fail(`PREVIEW_SERVER_NOT_READY=${lastError}`);
}

async function assertPortAvailable(port) {
  await new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once("error", () => reject(new Error(`PREVIEW_PORT_UNAVAILABLE=${port}`)));
    probe.listen(port, "127.0.0.1", () => probe.close(resolve));
  });
}

async function runReadOnlySmoke(config, child) {
  const localOrigin = `http://localhost:${config.port}`;
  await waitForUrl(`${localOrigin}/`, child);
  await waitForUrl(`${localOrigin}/topics`, child);
  if (config.readApiOrigin) {
    const response = await waitForUrl(`${localOrigin}/api/v2/topic-catalog?limit=1&offset=0`, child);
    const body = await response.json();
    if (!Array.isArray(body.items)) fail("REAL_READ_ONLY_PROXY_RESPONSE_INVALID");
  }
}

async function stopChild(child) {
  if (!child || child.exitCode !== null) return;
  if (process.platform === "win32") child.kill();
  else child.kill("SIGINT");
  await new Promise((resolve) => child.once("close", resolve));
}

async function main() {
  const config = parseReviewConfig();
  const env = runtimeEnvironment(config);
  let candidateSha = "UNBOUND_DIRTY_WORKTREE";
  let child = null;
  let stopRequested = false;

  try {
    await fs.rm(PREVIEW_RECORD, { force: true });
    if (config.mode === "EXACT_SHA_CANDIDATE") {
      candidateSha = await prepareExactCandidate(config, env);
    } else if (config.candidateRef) {
      candidateSha = await gitOutput(["rev-parse", "--short", "HEAD"]);
    }

    await assertPortAvailable(config.port);
    child = spawn(NPM, ["run", "dev", "--prefix", "apps/web", "--", "--host", "127.0.0.1", "--port", String(config.port)], {
      cwd: REPO_ROOT,
      env,
      stdio: "inherit",
      shell: process.platform === "win32",
    });
    child.on("error", (error) => { if (!stopRequested) console.error(error); });
    process.on("SIGINT", () => {
      stopRequested = true;
      void stopChild(child);
    });
    process.on("SIGTERM", () => {
      stopRequested = true;
      void stopChild(child);
    });

    await runReadOnlySmoke(config, child);
    console.log("");
    console.log("TOPICPILOT_PREVIEW_REVIEW=READY");
    console.log(`REVIEW_MODE=${config.mode}`);
    console.log(`PREVIEW_CANDIDATE_SHA=${candidateSha}`);
    console.log(`DATA_MODE=${config.dataMode}`);
    console.log(`DATA_TARGET=${config.readApiOrigin ?? "SYNTHETIC_SNAPSHOT"}`);
    console.log("LOCAL_PROXY_USED=" + (config.readApiOrigin ? "YES" : "NO"));
    console.log("DIAGNOSTICS_DEFAULT=OFF");
    console.log(`PREVIEW_URL=http://localhost:${config.port}`);
    console.log("STOP_COMMAND=Ctrl+C");
    console.log("");

    const exitCode = await new Promise((resolve) => child.once("close", (code) => resolve(code ?? 0)));
    if (!stopRequested && exitCode !== 0) fail(`PREVIEW_SERVER_EXITED=${exitCode}`);
  } finally {
    await stopChild(child);
    await fs.rm(PREVIEW_RECORD, { force: true });
  }
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) {
  main().catch((error) => {
    console.error(`PREVIEW_REVIEW=FAIL\n${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 1;
  });
}
