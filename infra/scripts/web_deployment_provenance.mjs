/** Fail-closed Web build, Sites successor and runtime evidence boundary. */
import { createHash, randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import { existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

export const AUTHORITY = "GITHUB_CANONICAL_MAIN";
export const SIDECAR = ".openai/release-provenance.json";
export const PUBLIC_PROOF = "client/__release.json";
const RESERVED = new Set([SIDECAR, PUBLIC_PROOF]);
const REQUIRED = ["canonicalSourceSha", "sitesParentSourceSha", "artifactDigest", "buildTimestamp", "deployedRuntimeSha"];
const DIGEST_POLICY = "sha256-sorted-path-byte-length-file-sha256-v1";
export const CI_WORKFLOW = ".github/workflows/web-artifact-verification.yml";
export const CI_REPOSITORY = "Xiezhou0828/topicpilot-platform";
const CI_ENVIRONMENT = "GITHUB_ACTIONS_ISOLATED_WORKER";
const GITHUB_ORIGINS = new Set([
  "https://github.com/Xiezhou0828/topicpilot-platform.git",
  "https://github.com/Xiezhou0828/topicpilot-platform",
  "git@github.com:Xiezhou0828/topicpilot-platform.git",
]);
const fail = (condition, code) => { if (!condition) throw new Error(code); };
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const json = (filename) => JSON.parse(readFileSync(filename, "utf8"));
const git = (root, args, encoding = "utf8") => execFileSync("git", args, {
  cwd: root, encoding, stdio: ["ignore", "pipe", "pipe"], maxBuffer: 64 * 1024 * 1024,
});
const gitText = (root, args) => git(root, args).trim();

export function exactSha(value, field) {
  fail(typeof value === "string" && /^[0-9a-f]{40}$/.test(value), `INVALID_${field}`);
  return value;
}

export function validateRecord(record, canonical, parent, { runtime = false, now = Date.now() } = {}) {
  fail(record && typeof record === "object" && !Array.isArray(record), "MISSING_PROVENANCE");
  for (const field of REQUIRED) fail(Object.hasOwn(record, field), `MISSING_${field}`);
  fail(record.schemaVersion === 1 && record.webSourceAuthority === AUTHORITY, "SOURCE_AUTHORITY_MISMATCH");
  fail(exactSha(record.canonicalSourceSha, "canonicalSourceSha") === exactSha(canonical, "canonicalSourceSha"), "CANONICAL_SHA_MISMATCH");
  fail(exactSha(record.sitesParentSourceSha, "sitesParentSourceSha") === exactSha(parent, "sitesParentSourceSha"), "SITES_PARENT_MISMATCH");
  fail(typeof record.artifactDigest === "string" && /^sha256:[0-9a-f]{64}$/.test(record.artifactDigest), "INVALID_ARTIFACT_DIGEST");
  const timestamp = typeof record.buildTimestamp === "string" ? Date.parse(record.buildTimestamp) : NaN;
  fail(Number.isFinite(timestamp) && new Date(timestamp).toISOString() === record.buildTimestamp && timestamp <= now, "INVALID_BUILD_TIMESTAMP");
  if (runtime) {
    fail(exactSha(record.deployedRuntimeSha, "deployedRuntimeSha") === canonical, "RUNTIME_SHA_MISMATCH");
  } else {
    fail(record.deployedRuntimeSha === null, "BUILD_CANNOT_ATTEST_RUNTIME");
  }
  return record;
}

export function artifactFiles(root, relative = "") {
  fail(lstatSync(root).isDirectory() && !lstatSync(root).isSymbolicLink(), "INVALID_ARTIFACT_ROOT");
  const files = [];
  for (const name of readdirSync(path.join(root, relative)).sort()) {
    fail(!name.includes("\\") && !/[\r\n]/.test(name), "UNSAFE_ARTIFACT_PATH");
    const item = path.posix.join(relative, name);
    const stat = lstatSync(path.join(root, item));
    fail(!stat.isSymbolicLink(), "ARTIFACT_SYMLINK_REJECTED");
    if (stat.isDirectory()) files.push(...artifactFiles(root, item));
    else {
      fail(stat.isFile(), "ARTIFACT_SPECIAL_FILE_REJECTED");
      if (RESERVED.has(item)) continue;
      const bytes = readFileSync(path.join(root, item));
      files.push({ path: item, bytes: bytes.length, sha256: sha256(bytes) });
    }
  }
  // Sort full paths, not platform locale or directory enumeration order.
  return files.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
}

export function verifyArtifact(root, canonical, parent) {
  const record = validateRecord(json(path.join(root, SIDECAR)), canonical, parent);
  fail(JSON.stringify(json(path.join(root, PUBLIC_PROOF))) === JSON.stringify(record), "PUBLIC_PROVENANCE_MISMATCH");
  fail(record.digestPolicy === DIGEST_POLICY, "UNKNOWN_DIGEST_POLICY");
  const files = artifactFiles(root);
  fail(files.some((file) => file.path === "server/index.js"), "MISSING_SERVER_ARTIFACT");
  fail(files.some((file) => /^client\/assets\/.+\.js$/.test(file.path)), "MISSING_CLIENT_ARTIFACT");
  fail(JSON.stringify(record.artifactFiles) === JSON.stringify(files), "ARTIFACT_MANIFEST_MISMATCH");
  fail(record.artifactDigest === `sha256:${sha256(JSON.stringify(files))}`, "ARTIFACT_DIGEST_MISMATCH");
  return record;
}

export function verifyCanonicalSource(root, canonical, runGit = gitText) {
  exactSha(canonical, "canonicalSourceSha");
  fail(GITHUB_ORIGINS.has(runGit(root, ["remote", "get-url", "origin"])), "NON_CANONICAL_GITHUB_ORIGIN");
  const main = runGit(root, ["ls-remote", "origin", "refs/heads/main"]).split(/\s+/);
  fail(main.length === 2 && main[1] === "refs/heads/main" && main[0] === canonical, "REMOTE_MAIN_SHA_MISMATCH");
  fail(runGit(root, ["rev-parse", "HEAD"]) === canonical, "SOURCE_HEAD_MISMATCH");
  fail(runGit(root, ["status", "--porcelain"]) === "", "DIRTY_CANONICAL_SOURCE");
}

function npmBuild(root) {
  if (process.platform === "win32") {
    const cli = path.join(path.dirname(process.execPath), "node_modules/npm/bin/npm-cli.js");
    execFileSync(process.execPath, [cli, "ci", "--prefix", "apps/web"], { cwd: root, stdio: "inherit" });
    execFileSync(process.execPath, [cli, "run", "build", "--prefix", "apps/web"], { cwd: root, stdio: "inherit" });
  } else {
    execFileSync("npm", ["ci", "--prefix", "apps/web"], { cwd: root, stdio: "inherit" });
    execFileSync("npm", ["run", "build", "--prefix", "apps/web"], { cwd: root, stdio: "inherit" });
  }
}

export function buildArtifact(root, canonical, parent, { verifySource = verifyCanonicalSource, build = npmBuild, now = () => new Date() } = {}) {
  exactSha(parent, "sitesParentSourceSha");
  verifySource(root, canonical);
  const dist = path.join(root, "apps/web/dist");
  // Never stamp a previous build. Preserve, rather than delete, old output.
  if (existsSync(dist)) {
    fail(lstatSync(dist).isDirectory() && !lstatSync(dist).isSymbolicLink(), "INVALID_EXISTING_DIST");
    const backup = path.join(root, "work/web-build-history", randomUUID());
    mkdirSync(path.dirname(backup), { recursive: true });
    renameSync(dist, backup);
  }
  const buildTimestamp = now().toISOString();
  build(root);
  verifySource(root, canonical);
  fail(!existsSync(path.join(dist, SIDECAR)) && !existsSync(path.join(dist, PUBLIC_PROOF)), "BUILDER_SUPPLIED_PROVENANCE_REJECTED");
  const files = artifactFiles(dist);
  const record = {
    schemaVersion: 1, webSourceAuthority: AUTHORITY, canonicalSourceSha: canonical,
    sitesParentSourceSha: parent, artifactDigest: `sha256:${sha256(JSON.stringify(files))}`,
    buildTimestamp, deployedRuntimeSha: null, digestPolicy: DIGEST_POLICY, artifactFiles: files,
  };
  const content = JSON.stringify(record, null, 2) + "\n";
  for (const filename of RESERVED) {
    mkdirSync(path.dirname(path.join(dist, filename)), { recursive: true });
    writeFileSync(path.join(dist, filename), content, { flag: "wx" });
  }
  return verifyArtifact(dist, canonical, parent);
}

export function verifySitesSuccessor(siteRoot, bundleRoot, record, sitesSource, currentSitesSource, runGit = gitText, readBlob = git, supportedPushProof = null) {
  exactSha(sitesSource, "sitesSuccessorSourceSha");
  fail([record.sitesParentSourceSha, sitesSource].includes(exactSha(currentSitesSource, "currentSitesSourceSha")), "SITES_CURRENT_SOURCE_MOVED");
  fail(runGit(siteRoot, ["status", "--porcelain"]) === "", "DIRTY_SITES_SUCCESSOR");
  fail(runGit(siteRoot, ["rev-parse", "HEAD"]) === sitesSource, "SITES_SUCCESSOR_HEAD_MISMATCH");
  fail(runGit(siteRoot, ["rev-list", "--parents", "-n", "1", "HEAD"]) === `${sitesSource} ${record.sitesParentSourceSha}`, "SITES_HISTORY_NOT_PRESERVED");
  if (supportedPushProof) {
    // The official Sites workflow owns authenticated push + subsequent
    // ls-remote verification; it intentionally does not create an origin.
    fail(supportedPushProof.commit_sha === sitesSource &&
      path.resolve(supportedPushProof.checkout_path) === path.resolve(siteRoot) &&
      supportedPushProof.project_id === json(path.join(siteRoot, ".openai/hosting.json")).project_id &&
      path.isAbsolute(supportedPushProof.archive) && existsSync(supportedPushProof.archive), "SITES_SUPPORTED_PUSH_EVIDENCE_MISMATCH");
  } else {
    const remote = runGit(siteRoot, ["ls-remote", "origin", "refs/heads/main"]).split(/\s+/);
    fail(remote.length === 2 && remote[0] === sitesSource && remote[1] === "refs/heads/main", "SITES_REMOTE_SOURCE_MISMATCH");
  }
  const prefix = `canonical-web-releases/${record.canonicalSourceSha}/`;
  const diff = runGit(siteRoot, ["diff", "--name-status", "HEAD^", "HEAD"]).split("\n");
  fail(diff.length > 0 && diff.every((line) => line.startsWith(`A\t${prefix}`)), "SITES_NON_ADDITIVE_CHANGE_REJECTED");
  const bundle = path.join(siteRoot, prefix, "bundle");
  const project = json(path.join(bundleRoot, ".openai/hosting.json")).project_id;
  fail(typeof project === "string" && project.length > 0 &&
    json(path.join(siteRoot, ".openai/hosting.json")).project_id === project, "SITES_PROJECT_ID_MISMATCH");
  fail(JSON.stringify(verifyArtifact(bundle, record.canonicalSourceSha, record.sitesParentSourceSha)) === JSON.stringify(record), "SITES_ARTIFACT_PROVENANCE_MISMATCH");
  // The supported packager publishes root dist, not the pinned history folder.
  fail(JSON.stringify(verifyArtifact(path.join(siteRoot, "dist"), record.canonicalSourceSha, record.sitesParentSourceSha)) === JSON.stringify(record), "SITES_PUBLISH_OUTPUT_MISMATCH");
  // Verify committed bytes, not only a possibly edited/ignored working tree.
  for (const filename of [...record.artifactFiles.map((file) => file.path), ...RESERVED]) {
    const committed = readBlob(siteRoot, ["show", `HEAD:${prefix}bundle/${filename}`], null);
    fail(sha256(committed) === sha256(readFileSync(path.join(bundleRoot, filename))), "SITES_COMMITTED_ARTIFACT_MISMATCH");
  }
  return sitesSource;
}

function runtimeOrigin(raw) {
  const url = new URL(raw);
  fail(url.protocol === "https:" && !url.username && !url.password && !url.search && !url.hash && url.pathname === "/", "INVALID_RUNTIME_ORIGIN");
  return url.origin;
}

export async function readRuntime(record, rawOrigin, { fetchImpl = fetch, now = () => new Date() } = {}) {
  validateRecord(record, record.canonicalSourceSha, record.sitesParentSourceSha);
  const origin = runtimeOrigin(rawOrigin);
  const get = async (route) => {
    const response = await fetchImpl(origin + route, { redirect: "error", cache: "no-store", signal: AbortSignal.timeout(30000) });
    fail(response.ok, "RUNTIME_READBACK_HTTP_FAILURE");
    return response;
  };
  const deployed = await (await get("/__release.json")).json();
  fail(JSON.stringify(deployed) === JSON.stringify(record), "RUNTIME_PROVENANCE_MISMATCH");
  const html = await (await get("/")).text();
  const scripts = [...html.matchAll(/<script\b[^>]*?\ssrc\s*=\s*["']([^"']+)["'][^>]*>/gi)].map((match) => match[1]);
  // Vinext emits inline module imports with canonical modulepreload links.
  // Bind actual served module references to the same strict byte manifest.
  const preloads = [...html.matchAll(/<link\b[^>]*>/gi)].filter((tag) => /\brel\s*=\s*["']modulepreload["']/i.test(tag[0]))
    .map((tag) => tag[0].match(/\bhref\s*=\s*["']([^"']+)["']/i)?.[1]).filter(Boolean);
  scripts.push(...preloads);
  fail(scripts.length > 0, "RUNTIME_HTML_HAS_NO_CANONICAL_MODULES");
  const verified = [];
  for (const src of new Set(scripts)) {
    const url = new URL(src, origin);
    fail(url.origin === origin && !url.search && !url.hash && /^\/assets\/.+\.js$/.test(url.pathname), "UNVERIFIABLE_RUNTIME_SCRIPT");
    const file = record.artifactFiles.find((item) => item.path === `client${url.pathname}`);
    fail(file, "RUNTIME_SCRIPT_NOT_IN_CANONICAL_ARTIFACT");
    const bytes = Buffer.from(await (await get(url.pathname)).arrayBuffer());
    fail(bytes.length === file.bytes && sha256(bytes) === file.sha256, "RUNTIME_SCRIPT_DIGEST_MISMATCH");
    verified.push({ path: file.path, sha256: file.sha256 });
  }
  const evidence = {
    schemaVersion: record.schemaVersion, webSourceAuthority: AUTHORITY,
    canonicalSourceSha: record.canonicalSourceSha, sitesParentSourceSha: record.sitesParentSourceSha,
    artifactDigest: record.artifactDigest, buildTimestamp: record.buildTimestamp,
    deployedRuntimeSha: deployed.canonicalSourceSha, runtimeUrl: origin,
    runtimeReadbackAt: now().toISOString(), verifiedRuntimeAssets: verified,
    artifactServerBytesVerification: "COMMITTED_SITES_BUNDLE_REQUIRED_SEPARATELY",
  };
  return validateRecord(evidence, record.canonicalSourceSha, record.sitesParentSourceSha, { runtime: true });
}

// CI is a separate, explicitly bounded verification surface, not a waiver of
// runtime verification. Trust the successful canonical workflow AND the exact
// GitHub artifact ZIP digest; never accept a standalone local receipt.
export function validateCiEvidence(record, receipt, run, artifact, archiveDigest) {
  validateRecord(receipt, record.canonicalSourceSha, record.sitesParentSourceSha, { runtime: true });
  fail(receipt.artifactDigest === record.artifactDigest && receipt.buildTimestamp === record.buildTimestamp, "CI_ARTIFACT_PROVENANCE_MISMATCH");
  fail(receipt.verificationEnvironment === CI_ENVIRONMENT && receipt.productionRuntimeVerified === false &&
    receipt.runtimeUrl === "https://localhost:8443", "CI_VERIFICATION_SURFACE_MISMATCH");
  const ci = receipt.githubActions;
  fail(ci && Number.isSafeInteger(ci.runId) && ci.runId > 0 && ci.runAttempt === 1 &&
    ci.repository === CI_REPOSITORY && ci.event === "workflow_dispatch" && ci.ref === "refs/heads/main" &&
    ci.workflowSha === record.canonicalSourceSha &&
    ci.workflowRef === `${CI_REPOSITORY}/${CI_WORKFLOW}@refs/heads/main`, "CI_RECEIPT_CONTEXT_MISMATCH");
  fail(run.id === ci.runId && run.run_attempt === ci.runAttempt && run.status === "completed" &&
    run.conclusion === "success" && run.event === "workflow_dispatch" && run.head_branch === "main" &&
    run.head_sha === record.canonicalSourceSha && run.path === CI_WORKFLOW &&
    run.repository?.full_name === CI_REPOSITORY && run.head_repository?.full_name === CI_REPOSITORY, "CI_RUN_NOT_CANONICAL_SUCCESS");
  fail(artifact.expired === false && artifact.name === `canonical-web-${record.canonicalSourceSha}-${ci.runId}-1` &&
    artifact.workflow_run?.id === ci.runId && artifact.workflow_run?.head_sha === record.canonicalSourceSha &&
    artifact.workflow_run?.head_branch === "main" && /^sha256:[0-9a-f]{64}$/.test(archiveDigest) &&
    artifact.digest === archiveDigest, "CI_ARCHIVE_DIGEST_OR_RUN_MISMATCH");
  const timestamp = Date.parse(receipt.runtimeReadbackAt);
  fail(Number.isFinite(timestamp) && timestamp >= Date.parse(record.buildTimestamp) &&
    timestamp < Date.parse(run.updated_at) + 1000 && timestamp < Date.parse(artifact.created_at) + 1000, "CI_READBACK_TIME_MISMATCH");
  fail(Array.isArray(receipt.verifiedRuntimeAssets) && receipt.verifiedRuntimeAssets.length > 0, "CI_RUNTIME_ASSETS_MISSING");
  const seen = new Set();
  for (const item of receipt.verifiedRuntimeAssets) {
    const file = record.artifactFiles.find((candidate) => candidate.path === item.path);
    fail(file && /^client\/assets\/.+\.js$/.test(item.path) && file.sha256 === item.sha256 && !seen.has(item.path), "CI_RUNTIME_ASSET_MISMATCH");
    seen.add(item.path);
  }
  return receipt;
}

export async function readCiArchive(record, archive, runId, artifactId, { fetchImpl = fetch, readEntry = (entry) =>
  execFileSync("tar", ["-xOf", archive, entry], { encoding: null, maxBuffer: 64 * 1024 * 1024 }) } = {}) {
  fail(Number.isSafeInteger(runId) && runId > 0 && Number.isSafeInteger(artifactId) && artifactId > 0, "INVALID_CI_IDENTIFIERS");
  const receipt = JSON.parse(readEntry("runtime-evidence.json").toString("utf8"));
  const get = async (route) => {
    const response = await fetchImpl(`https://api.github.com/repos/${CI_REPOSITORY}/${route}`, {
      headers: { Accept: "application/vnd.github+json", "User-Agent": "TopicPilot-Web-Provenance" },
      redirect: "error", cache: "no-store", signal: AbortSignal.timeout(30000),
    });
    fail(response.ok, "CI_EVIDENCE_HTTP_FAILURE");
    return response.json();
  };
  const run = await get(`actions/runs/${runId}`);
  const artifact = await get(`actions/artifacts/${artifactId}`);
  const evidence = validateCiEvidence(record, receipt, run, artifact, `sha256:${sha256(readFileSync(archive))}`);
  fail(evidence.githubActions.runId === runId && artifact.id === artifactId, "CI_EVIDENCE_IDENTIFIER_MISMATCH");
  // Bind all server/client files and both sidecars to the authenticated ZIP,
  // rather than trusting extraction or a locally generated receipt.
  for (const filename of [...record.artifactFiles.map((file) => file.path), ...RESERVED]) {
    const bytes = readEntry(`artifact/${filename}`);
    if (RESERVED.has(filename)) fail(JSON.stringify(JSON.parse(bytes.toString("utf8"))) === JSON.stringify(record), "CI_ARCHIVED_PROVENANCE_MISMATCH");
    else {
      const expected = record.artifactFiles.find((file) => file.path === filename);
      fail(bytes.length === expected.bytes && sha256(bytes) === expected.sha256, "CI_ARCHIVED_ARTIFACT_MISMATCH");
    }
  }
  return { ...evidence, ciArtifactId: artifactId, ciArchiveDigest: artifact.digest };
}

async function main() {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: Object.fromEntries([
    "repo-root", "canonical-source-sha", "sites-parent-source-sha", "artifact-dir", "sites-checkout",
    "sites-successor-source-sha", "sites-current-source-sha", "runtime-url", "sites-supported-push-proof",
    "ci-artifact-archive", "ci-run-id", "ci-artifact-id", "evidence-output",
  ].map((name) => [name, { type: "string" }])) });
  const command = positionals[0];
  fail(positionals.length === 1 && ["build", "prepublish", "readback", "ci-readback"].includes(command), "EXPECTED_BUILD_PREPUBLISH_OR_READBACK");
  const root = path.resolve(values["repo-root"] ?? ".");
  const canonical = exactSha(values["canonical-source-sha"], "canonicalSourceSha");
  const parent = exactSha(values["sites-parent-source-sha"], "sitesParentSourceSha");
  let result;
  if (command === "build") result = buildArtifact(root, canonical, parent);
  else {
    verifyCanonicalSource(root, canonical);
    fail(values["artifact-dir"], "MISSING_ARTIFACT_DIRECTORY");
    const bundle = path.resolve(values["artifact-dir"]);
    const record = verifyArtifact(bundle, canonical, parent);
    if (command === "prepublish") {
      fail(values["sites-checkout"] && values["sites-successor-source-sha"] && values["sites-current-source-sha"], "MISSING_SITES_SOURCE_EVIDENCE");
      verifySitesSuccessor(path.resolve(values["sites-checkout"]), bundle, record,
        values["sites-successor-source-sha"], values["sites-current-source-sha"], gitText, git,
        values["sites-supported-push-proof"] ? json(values["sites-supported-push-proof"]) : null);
    }
    if (command === "ci-readback") {
      fail(process.env.GITHUB_ACTIONS === "true" && process.env.GITHUB_EVENT_NAME === "workflow_dispatch" &&
        process.env.GITHUB_REF === "refs/heads/main" && process.env.GITHUB_SHA === canonical &&
        process.env.GITHUB_WORKFLOW_SHA === canonical && process.env.GITHUB_RUN_ATTEMPT === "1" &&
        process.env.GITHUB_REPOSITORY === CI_REPOSITORY &&
        process.env.GITHUB_WORKFLOW_REF === `${CI_REPOSITORY}/${CI_WORKFLOW}@refs/heads/main` &&
        values["runtime-url"] === "https://localhost:8443" && process.env.NODE_EXTRA_CA_CERTS && values["evidence-output"], "CI_RUN_CONTEXT_REJECTED");
      result = { ...await readRuntime(record, values["runtime-url"]), verificationEnvironment: CI_ENVIRONMENT,
        productionRuntimeVerified: false, githubActions: { repository: CI_REPOSITORY,
          runId: Number(process.env.GITHUB_RUN_ID), runAttempt: 1, workflowSha: process.env.GITHUB_WORKFLOW_SHA,
          workflowRef: process.env.GITHUB_WORKFLOW_REF, event: "workflow_dispatch", ref: "refs/heads/main" } };
      fail(Number.isSafeInteger(result.githubActions.runId) && result.githubActions.runId > 0, "INVALID_CI_IDENTIFIERS");
      verifyArtifact(bundle, canonical, parent);
      const output = path.resolve(values["evidence-output"]);
      fail(output.startsWith(path.join(root, "work") + path.sep), "CI_OUTPUT_OUTSIDE_WORK_DIRECTORY");
      mkdirSync(path.dirname(output), { recursive: true });
      writeFileSync(output, JSON.stringify(result, null, 2) + "\n", { flag: "wx" });
    } else if (command === "prepublish" && values["ci-artifact-archive"]) {
      fail(!values["runtime-url"] && values["ci-run-id"] && values["ci-artifact-id"], "AMBIGUOUS_RUNTIME_EVIDENCE");
      result = await readCiArchive(record, path.resolve(values["ci-artifact-archive"]), Number(values["ci-run-id"]), Number(values["ci-artifact-id"]));
    } else {
      fail(values["runtime-url"] && !values["ci-artifact-archive"], "MISSING_RUNTIME_READBACK");
      result = await readRuntime(record, values["runtime-url"]);
    }
    // Recheck main after network I/O. A moved canonical base stops promotion.
    verifyCanonicalSource(root, canonical);
    if (command === "prepublish") {
      verifySitesSuccessor(path.resolve(values["sites-checkout"]), bundle, record,
        values["sites-successor-source-sha"], values["sites-current-source-sha"], gitText, git,
        values["sites-supported-push-proof"] ? json(values["sites-supported-push-proof"]) : null);
      result.sitesSuccessorSourceSha = values["sites-successor-source-sha"];
      result.sitesObservedSourceSha = values["sites-current-source-sha"];
      result.publishAllowed = true;
    }
  }
  console.log(JSON.stringify({ status: "PASS", phase: command, ...result }));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    // Do not print arbitrary git/network errors or credential-bearing content.
    console.error("WEB_PROVENANCE_GUARD=FAIL_CLOSED; publication is not authorized. Check lineage inputs and protected evidence.");
    if (/^[A-Z][A-Z0-9_]*$/.test(error.message)) console.error(`WEB_PROVENANCE_FAILURE=${error.message}`);
    process.exitCode = 1;
  });
}
