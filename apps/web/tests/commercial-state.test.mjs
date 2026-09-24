import assert from "node:assert/strict";
import test from "node:test";
import { commercialDataState, commercialStateLabel } from "../app/lib/commercial-state.mjs";

const state = (input) => commercialDataState(input).state;

test("shared mapping covers canonical transport and authority states", () => {
  assert.equal(state({ transport: "LOADING" }), "LOADING");
  assert.deepEqual(commercialDataState({ transport: "ERROR", reasonCode: "HTTP_503" }), { state: "ERROR", reason: null, reasonCode: "HTTP_503", retryable: true });
  assert.equal(state({ status: "AVAILABLE", rowCount: 1 }), "AVAILABLE");
  assert.equal(state({ publication: "PUBLISHED", rowCount: 1 }), "PUBLISHED");
  assert.equal(state({ status: "AVAILABLE", rowCount: 0 }), "EMPTY");
  assert.equal(state({ status: "PARTIAL", rowCount: 3 }), "PARTIAL");
  assert.equal(state({ status: "AVAILABLE", freshness: "STALE", rowCount: 3 }), "STALE");
  assert.equal(state({ status: "STALE", rowCount: 3 }), "STALE");
  assert.equal(state({ status: "UNAVAILABLE", rowCount: 0 }), "UNAVAILABLE");
  assert.equal(state({ status: "NOT_APPLICABLE" }), "NOT_APPLICABLE");
});

test("reason text is preserved but never used to invent a stronger state", () => {
  assert.deepEqual(commercialDataState({ status: "UNAVAILABLE", reasonCode: "UNKNOWN_REASON", reason: "opaque" }), { state: "UNAVAILABLE", reason: "opaque", reasonCode: "UNKNOWN_REASON", retryable: false });
  assert.equal(state({ status: "MYSTERY", reasonCode: "LOOKS_AVAILABLE", rowCount: 2 }), "UNAVAILABLE");
  assert.equal(commercialStateLabel("NOT_APPLICABLE"), "不適用");
});
