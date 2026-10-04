import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  AUTHORITY, CI_REPOSITORY, CI_WORKFLOW, artifactFiles, readCiArchive,
  readRuntime, validateCiEvidence, validateRecord, verifyArtifact, verifyCanonicalSource,
} from "../web_deployment_provenance.mjs";

const canonical = "a".repeat(40);
const parent = "b".repeat(40);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const bytes = Buffer.from("export const fixture = 'synthetic provenance test';\n");
const file = { path: "client/assets/test.js", bytes: bytes.length, sha256: digest(bytes) };
const record = {
  schemaVersion: 1, webSourceAuthority: AUTHORITY, canonicalSourceSha: canonical,
  sitesParentSourceSha: parent, artifactDigest: `sha256:${digest(JSON.stringify([file]))}`,
  buildTimestamp: "2026-10-04T10:00:00.000Z", deployedRuntimeSha: null,
  digestPolicy: "sha256-sorted-path-byte-length-file-sha256-v1", artifactFiles: [file],
};
const clone = (value) => structuredClone(value);
const html = '<link href="/assets/test.js" rel="modulepreload">';
const fetchRuntime = ({ markup = html, proof = record, asset = bytes, status = 200 } = {}) => async (url) => {
  const route = new URL(url).pathname;
  return new Response(route === "/" ? markup : route === "/__release.json" ? JSON.stringify(proof) : asset, { status });
};
function fixtures() {
  const archive = Buffer.from("synthetic test archive, not a credential");
  const receipt = {
    ...record, deployedRuntimeSha: canonical, runtimeUrl: "https://localhost:8443",
    runtimeReadbackAt: "2026-10-04T10:01:00.000Z", verificationEnvironment: "GITHUB_ACTIONS_ISOLATED_WORKER",
    productionRuntimeVerified: false, verifiedRuntimeAssets: [{ path: file.path, sha256: file.sha256 }],
    githubActions: { repository: CI_REPOSITORY, runId: 123, runAttempt: 1, workflowSha: canonical,
      workflowRef: `${CI_REPOSITORY}/${CI_WORKFLOW}@refs/heads/main`, event: "workflow_dispatch", ref: "refs/heads/main" },
  };
  const run = { id: 123, run_attempt: 1, status: "completed", conclusion: "success", event: "workflow_dispatch",
    head_branch: "main", head_sha: canonical, path: CI_WORKFLOW, repository: { full_name: CI_REPOSITORY },
    head_repository: { full_name: CI_REPOSITORY }, updated_at: "2026-10-04T10:03:00.000Z" };
  const artifact = { id: 321, expired: false, name: `canonical-web-${canonical}-123-1`,
    created_at: "2026-10-04T10:02:00.000Z", digest: `sha256:${digest(archive)}`,
    workflow_run: { id: 123, head_sha: canonical, head_branch: "main" } };
  return { receipt, run, artifact, archive };
}
test("Vinext modulepreload runtime bytes retain strict canonical binding", async () => {
  const evidence = await readRuntime(record, "https://preview.test", { fetchImpl: fetchRuntime() });
  assert.equal(evidence.deployedRuntimeSha, canonical);
  assert.equal(evidence.artifactDigest, record.artifactDigest);
  assert.deepEqual(evidence.verifiedRuntimeAssets, [{ path: file.path, sha256: file.sha256 }]);
});
for (const [name, options, error] of [
  ["wrong asset bytes", { asset: Buffer.from("wrong") }, "RUNTIME_SCRIPT_DIGEST_MISMATCH"],
  ["wrong source", { proof: { ...record, canonicalSourceSha: parent } }, "RUNTIME_PROVENANCE_MISMATCH"],
  ["no modules", { markup: "<html>none</html>" }, "RUNTIME_HTML_HAS_NO_CANONICAL_MODULES"],
  ["external module", { markup: '<link rel="modulepreload" href="https://external.test/assets/test.js">' }, "UNVERIFIABLE_RUNTIME_SCRIPT"],
  ["unknown module", { markup: '<link rel="modulepreload" href="/assets/unknown.js">' }, "RUNTIME_SCRIPT_NOT_IN_CANONICAL_ARTIFACT"],
  ["query string module", { markup: '<link rel="modulepreload" href="/assets/test.js?x=1">' }, "UNVERIFIABLE_RUNTIME_SCRIPT"],
  ["HTTP failure", { status: 503 }, "RUNTIME_READBACK_HTTP_FAILURE"],
]) test(`runtime rejects ${name}`, async () => {
  await assert.rejects(readRuntime(record, "https://preview.test", { fetchImpl: fetchRuntime(options) }), new RegExp(error));
});
test("inline import and script src remain supported with same byte guard", async () => {
  const evidence = await readRuntime(record, "https://preview.test", {
    fetchImpl: fetchRuntime({ markup: html + '<script src="/assets/test.js"></script>' }),
  });
  assert.equal(evidence.verifiedRuntimeAssets.length, 1);
});
test("HTTP preview origin is not silently allowed", async () => {
  await assert.rejects(readRuntime(record, "http://localhost:8443", { fetchImpl: fetchRuntime() }), /INVALID_RUNTIME_ORIGIN/);
});
test("successful canonical CI evidence is explicitly NOT a Production runtime claim", () => {
  const { receipt, run, artifact } = fixtures();
  assert.equal(validateCiEvidence(record, receipt, run, artifact, artifact.digest).productionRuntimeVerified, false);
});
for (const [name, mutate] of [
  ["failed workflow", (f) => { f.run.conclusion = "failure"; }],
  ["running workflow", (f) => { f.run.status = "in_progress"; }],
  ["wrong canonical workflow SHA", (f) => { f.run.head_sha = parent; }],
  ["different workflow file", (f) => { f.run.path = ".github/workflows/ci.yml"; }],
  ["PR workflow", (f) => { f.run.event = "pull_request"; }],
  ["wrong branch", (f) => { f.run.head_branch = "candidate"; }],
  ["fork repository", (f) => { f.run.head_repository.full_name = "untrusted/fork"; }],
  ["re-run receipt", (f) => { f.receipt.githubActions.runAttempt = 2; }],
  ["re-run workflow", (f) => { f.run.run_attempt = 2; }],
  ["wrong receipt source", (f) => { f.receipt.githubActions.workflowSha = parent; }],
  ["wrong receipt repository", (f) => { f.receipt.githubActions.repository = "untrusted/fork"; }],
  ["wrong receipt workflow ref", (f) => { f.receipt.githubActions.workflowRef += "-other"; }],
  ["fabricated Production claim", (f) => { f.receipt.productionRuntimeVerified = true; }],
  ["wrong artifact digest", (f) => { f.artifact.digest = `sha256:${digest("different")}`; }],
  ["wrong artifact run", (f) => { f.artifact.workflow_run.id = 124; }],
  ["wrong artifact source", (f) => { f.artifact.workflow_run.head_sha = parent; }],
  ["wrong artifact name", (f) => { f.artifact.name = "generic-build"; }],
  ["expired artifact", (f) => { f.artifact.expired = true; }],
  ["wrong Sites parent", (f) => { f.receipt.sitesParentSourceSha = canonical; }],
  ["wrong build digest", (f) => { f.receipt.artifactDigest = `sha256:${digest("another build")}`; }],
  ["missing verified assets", (f) => { f.receipt.verifiedRuntimeAssets = []; }],
  ["wrong verified asset", (f) => { f.receipt.verifiedRuntimeAssets[0].sha256 = digest("wrong"); }],
  ["duplicate verified asset", (f) => { f.receipt.verifiedRuntimeAssets.push(clone(f.receipt.verifiedRuntimeAssets[0])); }],
  ["readback after upload", (f) => { f.receipt.runtimeReadbackAt = "2026-10-04T11:00:00.000Z"; }],
]) test(`CI evidence fails closed for ${name}`, () => {
  const f = fixtures();
  const archiveDigest = f.artifact.digest;
  mutate(f);
  assert.throws(() => validateCiEvidence(record, f.receipt, f.run, f.artifact, archiveDigest));
});
test("archive digest AND every archived byte are verified against live GitHub metadata", async (t) => {
  const root = mkdtempSync(path.join(os.tmpdir(), "topicpilot-provenance-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const f = fixtures();
  const filename = path.join(root, "fixture.zip");
  writeFileSync(filename, f.archive);
  const entry = (name) => name === "runtime-evidence.json" ? Buffer.from(JSON.stringify(f.receipt)) :
    name.endsWith(file.path) ? bytes : Buffer.from(JSON.stringify(record));
  const fetchImpl = async (url) => new Response(JSON.stringify(url.includes("actions/runs/") ? f.run : f.artifact));
  const evidence = await readCiArchive(record, filename, 123, 321, { fetchImpl, readEntry: entry });
  assert.equal(evidence.ciArtifactId, 321);
  await assert.rejects(readCiArchive(record, filename, 123, 321, {
    fetchImpl, readEntry: (name) => name.endsWith(file.path) ? Buffer.from("tampered") : entry(name),
  }), /CI_ARCHIVED_ARTIFACT_MISMATCH/);
  writeFileSync(filename, "tampered archive");
  await assert.rejects(readCiArchive(record, filename, 123, 321, { fetchImpl, readEntry: entry }), /CI_ARCHIVE_DIGEST_OR_RUN_MISMATCH/);
});
test("live GitHub metadata unavailable rejects a local receipt", async (t) => {
  const root = mkdtempSync(path.join(os.tmpdir(), "topicpilot-provenance-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const f = fixtures();
  const filename = path.join(root, "fixture.zip");
  writeFileSync(filename, f.archive);
  await assert.rejects(readCiArchive(record, filename, 123, 321, {
    fetchImpl: async () => new Response("denied", { status: 403 }),
    readEntry: () => Buffer.from(JSON.stringify(f.receipt)),
  }), /CI_EVIDENCE_HTTP_FAILURE/);
});
test("canonical source still requires clean exact main and origin", () => {
  const outputs = {
    "remote get-url origin": `https://github.com/${CI_REPOSITORY}.git`,
    "ls-remote origin refs/heads/main": `${canonical}\trefs/heads/main`,
    "rev-parse HEAD": canonical, "status --porcelain": "",
  };
  const git = (_, args) => outputs[args.join(" ")];
  verifyCanonicalSource("fixture", canonical, git);
  outputs["status --porcelain"] = " M source.js";
  assert.throws(() => verifyCanonicalSource("fixture", canonical, git), /DIRTY_CANONICAL_SOURCE/);
  outputs["status --porcelain"] = "";
  outputs["ls-remote origin refs/heads/main"] = `${parent}\trefs/heads/main`;
  assert.throws(() => verifyCanonicalSource("fixture", canonical, git), /REMOTE_MAIN_SHA_MISMATCH/);
});
test("artifact manifest includes server bytes, sidecars cannot self-attest runtime", (t) => {
  const root = mkdtempSync(path.join(os.tmpdir(), "topicpilot-provenance-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const directory of ["server", "client/assets", ".openai"]) mkdirSync(path.join(root, directory), { recursive: true });
  writeFileSync(path.join(root, "server/index.js"), "export default {fetch(){return new Response('synthetic')}}");
  writeFileSync(path.join(root, file.path), bytes);
  const files = artifactFiles(root);
  const proof = { ...record, artifactFiles: files, artifactDigest: `sha256:${digest(JSON.stringify(files))}` };
  for (const target of [".openai/release-provenance.json", "client/__release.json"]) writeFileSync(path.join(root, target), JSON.stringify(proof));
  verifyArtifact(root, canonical, parent);
  writeFileSync(path.join(root, "server/index.js"), "tampered");
  assert.throws(() => verifyArtifact(root, canonical, parent), /ARTIFACT_MANIFEST_MISMATCH/);
  assert.throws(() => validateRecord({ ...proof, deployedRuntimeSha: canonical }, canonical, parent), /BUILD_CANNOT_ATTEST_RUNTIME/);
  assert.equal(readFileSync(path.join(root, file.path)).length, file.bytes);
});
