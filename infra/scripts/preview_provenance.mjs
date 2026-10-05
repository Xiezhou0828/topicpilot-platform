/** Build and verify a non-Production Preview provenance record. */
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

export const PREVIEW_SCHEMA_VERSION = 1;
export const PREVIEW_RECORD = "__preview.json";
const SHA_RE = /^[0-9a-f]{40}$/;

const fail = (condition, code) => {
  if (!condition) throw new Error(code);
};

export function exactSha(value, field = "candidateSha") {
  fail(typeof value === "string" && SHA_RE.test(value), `INVALID_${field}`);
  return value;
}

function normalizedApiOrigin(raw) {
  if (!raw) return null;
  const url = new URL(raw);
  const local = url.hostname === "localhost" || url.hostname === "127.0.0.1";
  fail((url.protocol === "https:" || (url.protocol === "http:" && local)) &&
    !url.username && !url.password && !url.search && !url.hash && url.pathname === "/", "INVALID_PREVIEW_API_ORIGIN");
  return url.origin;
}

function gitText(root, args) {
  return execFileSync("git", args, { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
}

export function verifyCandidateCheckout(repoRoot, candidateSha, runGit = gitText) {
  const expected = exactSha(candidateSha);
  fail(runGit(repoRoot, ["rev-parse", "HEAD"]) === expected, "PREVIEW_CHECKOUT_SHA_MISMATCH");
  return expected;
}

export function buildPreviewRecord({ candidateSha, candidateRef = null, apiBaseUrl = "", buildTimestamp = new Date().toISOString() }) {
  const sha = exactSha(candidateSha);
  const timestamp = Date.parse(buildTimestamp);
  fail(Number.isFinite(timestamp) && new Date(timestamp).toISOString() === buildTimestamp, "INVALID_PREVIEW_BUILD_TIMESTAMP");
  const apiOrigin = normalizedApiOrigin(apiBaseUrl);
  return {
    schemaVersion: PREVIEW_SCHEMA_VERSION,
    previewSourceAuthority: "GITHUB_CANDIDATE_REF",
    candidateGitSha: sha,
    candidateRef: typeof candidateRef === "string" && candidateRef.trim() ? candidateRef.trim() : null,
    buildTimestamp,
    apiTarget: apiOrigin,
    dataMode: apiOrigin ? "READ_ONLY_API_TARGET" : "SYNTHETIC_SNAPSHOT",
    previewWriteAuthority: "NONE",
    productionPromotion: "NOT_AUTHORIZED_NOT_EXECUTED",
    previewReferenceType: "GITHUB_ACTIONS_ARTIFACT",
  };
}

export function writePreviewRecord(outputPath, record) {
  const serialized = JSON.stringify(record, null, 2) + "\n";
  mkdirSync(path.dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, serialized, { flag: "wx" });
  return record;
}

export function readPreviewRecord(filename) {
  return JSON.parse(readFileSync(filename, "utf8"));
}

export function validatePreviewRecord(record, candidateSha) {
  const expected = exactSha(candidateSha);
  fail(record && typeof record === "object" && !Array.isArray(record), "MISSING_PREVIEW_RECORD");
  fail(record.schemaVersion === PREVIEW_SCHEMA_VERSION, "PREVIEW_SCHEMA_MISMATCH");
  fail(record.previewSourceAuthority === "GITHUB_CANDIDATE_REF", "PREVIEW_SOURCE_AUTHORITY_MISMATCH");
  fail(exactSha(record.candidateGitSha) === expected, "PREVIEW_CANDIDATE_SHA_MISMATCH");
  fail(record.previewWriteAuthority === "NONE", "PREVIEW_WRITE_AUTHORITY_NOT_EMPTY");
  fail(record.productionPromotion === "NOT_AUTHORIZED_NOT_EXECUTED", "PREVIEW_PRODUCTION_BOUNDARY_MISMATCH");
  fail(["SYNTHETIC_SNAPSHOT", "READ_ONLY_API_TARGET"].includes(record.dataMode), "INVALID_PREVIEW_DATA_MODE");
  if (record.dataMode === "SYNTHETIC_SNAPSHOT") fail(record.apiTarget === null, "SYNTHETIC_PREVIEW_HAS_API_TARGET");
  else fail(typeof record.apiTarget === "string", "READ_ONLY_PREVIEW_API_TARGET_MISSING");
  const timestamp = Date.parse(record.buildTimestamp);
  fail(Number.isFinite(timestamp) && new Date(timestamp).toISOString() === record.buildTimestamp, "INVALID_PREVIEW_BUILD_TIMESTAMP");
  return record;
}

export function verifyPreviewArtifact(artifactDir, candidateSha) {
  const record = readPreviewRecord(path.join(artifactDir, "client", PREVIEW_RECORD));
  return validatePreviewRecord(record, candidateSha);
}

function main() {
  const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: {
      "repo-root": { type: "string" },
      "candidate-sha": { type: "string" },
      "candidate-ref": { type: "string" },
      "api-base-url": { type: "string" },
      output: { type: "string" },
      "artifact-dir": { type: "string" },
    },
  });
  const command = positionals[0];
  fail(command === "write" || command === "verify", "INVALID_PREVIEW_COMMAND");
  const candidateSha = exactSha(values["candidate-sha"]);
  if (command === "write") {
    fail(typeof values.output === "string" && values.output.length > 0, "MISSING_PREVIEW_OUTPUT");
    const repoRoot = path.resolve(values["repo-root"] ?? ".");
    verifyCandidateCheckout(repoRoot, candidateSha);
    const record = buildPreviewRecord({
      candidateSha,
      candidateRef: values["candidate-ref"] ?? null,
      apiBaseUrl: values["api-base-url"] ?? "",
    });
    writePreviewRecord(path.resolve(values.output), record);
    console.log(JSON.stringify({ status: "PASS", record }));
    return;
  }
  fail(typeof values["artifact-dir"] === "string" && values["artifact-dir"].length > 0, "MISSING_PREVIEW_ARTIFACT_DIR");
  const record = verifyPreviewArtifact(path.resolve(values["artifact-dir"]), candidateSha);
  console.log(JSON.stringify({ status: "PASS", record }));
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  try {
    main();
  } catch (error) {
    console.error("PREVIEW_PROVENANCE=FAIL_CLOSED");
    if (/^[A-Z][A-Z0-9_]*$/.test(error.message)) console.error(`PREVIEW_PROVENANCE_FAILURE=${error.message}`);
    process.exitCode = 1;
  }
}
