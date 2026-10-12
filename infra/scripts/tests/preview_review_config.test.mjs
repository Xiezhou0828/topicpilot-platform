import assert from "node:assert/strict";
import test from "node:test";

import { parseReviewConfig } from "../preview_review.mjs";

test("Preview review can split formal stock reads from an isolated financial read API", () => {
  const config = parseReviewConfig([
    "--mode", "iterative",
    "--read-api-origin", "https://topicpilot-api.onrender.com/",
    "--financial-api-origin", "http://127.0.0.1:8001/",
    "--port", "4320",
  ]);

  assert.equal(config.readApiOrigin, "https://topicpilot-api.onrender.com");
  assert.equal(config.financialApiOrigin, "http://127.0.0.1:8001");
  assert.equal(config.dataMode, "REAL_READ_ONLY");
  assert.equal(config.port, 4320);
});

test("Preview review rejects a non-loopback HTTP financial API origin", () => {
  assert.throws(
    () => parseReviewConfig(["--financial-api-origin", "http://api.example.test"]),
    /PREVIEW_READ_API_ORIGIN_MUST_BE_HTTPS_OR_LOCAL_LOOPBACK/,
  );
});
