import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  buildPreviewRecord,
  validatePreviewRecord,
  verifyCandidateCheckout,
  verifyPreviewArtifact,
  writePreviewRecord,
} from "../preview_provenance.mjs";

const sha = "a".repeat(40);

test("synthetic Preview records are explicit and have no API target", () => {
  const record = buildPreviewRecord({ candidateSha: sha, candidateRef: "feature/topic-ui" });
  assert.equal(record.dataMode, "SYNTHETIC_SNAPSHOT");
  assert.equal(record.apiTarget, null);
  assert.equal(record.previewWriteAuthority, "NONE");
  assert.equal(validatePreviewRecord(record, sha), record);
});

test("optional Preview API target is normalized as read-only origin metadata", () => {
  const record = buildPreviewRecord({ candidateSha: sha, apiBaseUrl: "https://staging.example.test/" });
  assert.equal(record.dataMode, "READ_ONLY_API_TARGET");
  assert.equal(record.apiTarget, "https://staging.example.test");
  assert.doesNotThrow(() => validatePreviewRecord(record, sha));
});

for (const [name, value] of [
  ["invalid SHA", "not-a-sha"],
  ["HTTP remote API", "http://api.example.test"],
  ["API path", "https://api.example.test/v1"],
  ["API credentials", "https://user:pass@api.example.test"],
]) {
  test(`Preview rejects ${name}`, () => {
    assert.throws(() => buildPreviewRecord({ candidateSha: sha, apiBaseUrl: value }));
  });
}

test("candidate checkout must match the requested SHA", () => {
  assert.equal(verifyCandidateCheckout("fixture", sha, () => sha), sha);
  assert.throws(() => verifyCandidateCheckout("fixture", sha, () => "b".repeat(40)), /PREVIEW_CHECKOUT_SHA_MISMATCH/);
});

test("built artifact exposes the same candidate record", () => {
  const root = mkdtempSync(path.join(os.tmpdir(), "topicpilot-preview-"));
  try {
    mkdirSync(path.join(root, "client"), { recursive: true });
    const record = buildPreviewRecord({ candidateSha: sha });
    writePreviewRecord(path.join(root, "client", "__preview.json"), record);
    assert.deepEqual(verifyPreviewArtifact(root, sha), record);
    assert.throws(() => verifyPreviewArtifact(root, "b".repeat(40)), /PREVIEW_CANDIDATE_SHA_MISMATCH/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
