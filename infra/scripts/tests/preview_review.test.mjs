import assert from "node:assert/strict";
import test from "node:test";

import {
  assertExactReviewState,
  parseReviewConfig,
} from "../preview_review.mjs";

test("parses iterative synthetic review mode explicitly", () => {
  assert.deepEqual(parseReviewConfig(["--mode", "iterative", "--port", "3010"]), {
    mode: "ITERATIVE_LOCAL",
    candidateRef: null,
    readApiOrigin: null,
    port: 3010,
    skipInstall: false,
    dataMode: "REPRESENTATIVE_SYNTHETIC",
  });
});

test("parses exact SHA real read-only review mode", () => {
  assert.deepEqual(parseReviewConfig([
    "--mode", "exact-sha",
    "--candidate-ref", "8894138fc930b4512541cacd5214162cd66b4c8f",
    "--read-api-origin", "https://topicpilot-api.onrender.com",
    "--skip-install",
  ]), {
    mode: "EXACT_SHA_CANDIDATE",
    candidateRef: "8894138fc930b4512541cacd5214162cd66b4c8f",
    readApiOrigin: "https://topicpilot-api.onrender.com",
    port: 3000,
    skipInstall: true,
    dataMode: "REAL_READ_ONLY",
  });
});

test("exact SHA mode rejects mismatch and dirty state", () => {
  assert.equal(assertExactReviewState({
    candidateSha: "abc",
    headSha: "abc",
    status: "",
  }), true);
  assert.throws(
    () => assertExactReviewState({ candidateSha: "abc", headSha: "def", status: "" }),
    /EXACT_SHA_CHECKOUT_MISMATCH/,
  );
  assert.throws(
    () => assertExactReviewState({ candidateSha: "abc", headSha: "abc", status: " M file" }),
    /EXACT_SHA_REVIEW_REQUIRES_CLEAN_WORKTREE/,
  );
});

