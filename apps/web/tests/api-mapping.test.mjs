import assert from "node:assert/strict";
import test from "node:test";
import { mapDataStatus, mapStock, nullableNumber, unwrapItems } from "../app/lib/mapping.mjs";

test("missing numeric values stay null instead of becoming zero", () => {
  assert.equal(nullableNumber(null), null);
  assert.equal(nullableNumber(undefined), null);
  assert.equal(nullableNumber(""), null);
  assert.equal(nullableNumber("not-a-number"), null);
  assert.equal(nullableNumber("0"), 0);
});

test("stock mapper accepts snake_case without inventing missing values", () => {
  const stock = mapStock({
    stock_code: "SYN-900",
    stock_name: "匿名測試",
    close_price: null,
    change_pct: "1.25",
    volume_ratio: "",
    topics: [{ name: "測試題材" }],
  });
  assert.equal(stock.code, "SYN-900");
  assert.equal(stock.price, null);
  assert.equal(stock.changePct, 1.25);
  assert.equal(stock.volumeRatio, null);
  assert.deepEqual(stock.topicNames, ["測試題材"]);
});

test("data status mapper preserves contract metadata and null counts", () => {
  const status = mapDataStatus({ data: {
    data_date: "2026-07-31",
    contract_version: "enterprise_bundle.v1",
    api_status: "healthy",
    database_status: "degraded",
    counts: { stock_count: null, topic_count: 5 },
  } });
  assert.equal(status.bundleVersion, "enterprise_bundle.v1");
  assert.equal(status.counts.stocks, null);
  assert.equal(status.counts.topics, 5);
});

test("list unwrapping supports plain and envelope responses", () => {
  assert.deepEqual(unwrapItems([1, 2]), [1, 2]);
  assert.deepEqual(unwrapItems({ items: [3] }), [3]);
  assert.deepEqual(unwrapItems({ data: { items: [4] } }), [4]);
  assert.deepEqual(unwrapItems({}), []);
});
