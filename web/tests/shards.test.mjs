import test from "node:test";
import assert from "node:assert/strict";
import { createShardCache } from "../shards.js";
import { needsShards, parseQuery } from "../query.js";

test("concurrent requests for one shard fetch it once", async () => {
  let calls = 0;
  const get = createShardCache(async (key) => {
    calls++;
    await new Promise((r) => setTimeout(r, 5));
    return [key];
  });
  const [a, b] = await Promise.all([get(1), get(1)]);
  assert.equal(calls, 1);
  assert.deepEqual(a, b);
});

test("a failed fetch is not cached and can be retried", async () => {
  let calls = 0;
  const get = createShardCache(async () => {
    calls++;
    if (calls === 1) throw new Error("HTTP 404");
    return ["ok"];
  });
  await assert.rejects(get(1), /404/);
  assert.deepEqual(await get(1), ["ok"]);
});

test("needsShards: name-only queries stay on names.json", () => {
  assert.equal(needsShards(parseQuery("kinase species:donovani"), false), false);
  assert.equal(needsShards(parseQuery("id:/^LdBPK/"), false), false);
});

test("needsShards: annotation filters, the checkbox and colon IDs load shards", () => {
  assert.equal(needsShards(parseQuery("type:tRNA"), false), true);
  assert.equal(needsShards(parseQuery("ec:2.7"), false), true);
  assert.equal(needsShards(parseQuery("kinase"), true), true);
  assert.equal(needsShards(parseQuery("GeneID:12981166"), false), true);
});
