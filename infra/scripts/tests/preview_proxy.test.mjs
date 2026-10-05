import assert from "node:assert/strict";
import test from "node:test";

import {
  createReadOnlyPreviewProxy,
  isAllowedPreviewProxyPath,
  isReadOnlyPreviewMethod,
  normalizeReadOnlyApiOrigin,
} from "../preview_proxy.mjs";

test("accepts HTTPS origins and local loopback origins", () => {
  assert.equal(normalizeReadOnlyApiOrigin("https://topicpilot-api.onrender.com"), "https://topicpilot-api.onrender.com");
  assert.equal(normalizeReadOnlyApiOrigin("http://localhost:8000"), "http://localhost:8000");
  assert.equal(normalizeReadOnlyApiOrigin("http://127.0.0.1:8000"), "http://127.0.0.1:8000");
});

test("rejects unsafe or non-origin upstream targets", () => {
  for (const value of [
    "http://example.com",
    "https://user:pass@example.com",
    "https://example.com/api",
    "https://example.com/?write=1",
  ]) {
    assert.throws(() => normalizeReadOnlyApiOrigin(value));
  }
});

test("allows only read methods and fixed API path prefixes", () => {
  assert.equal(isReadOnlyPreviewMethod("GET"), true);
  assert.equal(isReadOnlyPreviewMethod("HEAD"), true);
  assert.equal(isReadOnlyPreviewMethod("POST"), false);
  assert.equal(isReadOnlyPreviewMethod("OPTIONS"), false);

  assert.equal(isAllowedPreviewProxyPath("/api/v2/topic-catalog"), true);
  assert.equal(isAllowedPreviewProxyPath("/api/v1/snapshot/latest"), true);
  assert.equal(isAllowedPreviewProxyPath("/api/v1/admin"), false);
  assert.equal(isAllowedPreviewProxyPath("/proxy"), false);
});

test("builds a fixed-target proxy with a guard plugin", () => {
  const result = createReadOnlyPreviewProxy("https://topicpilot-api.onrender.com");
  assert.equal(result.target, "https://topicpilot-api.onrender.com");
  assert.deepEqual(Object.keys(result.proxy).sort(), [
    "/api/v1/snapshot",
    "/api/v1/topic-intelligence",
    "/api/v2",
  ]);
  assert.equal(result.plugin.name, "topicpilot-preview-read-only-proxy-guard");
});

