import test from "node:test";
import assert from "node:assert/strict";
import { buildRelatedIndex, exactQuery, related } from "../related.js";

// [genome index, id, name, product]
const names = [
  [0, "a1", "a1", "beta tubulin"],
  [0, "a2", "a2", "beta tubulin"],
  [1, "b1", "a1", "beta tubulin"],
  [2, "c1", "c1", "Beta tubulin"],
  [2, "c2", "c2", ""],
];
const index = buildRelatedIndex(names);

test("related counts the same product in other genes, by genome, excluding the gene itself", () => {
  const r = related(index, { name: "a1", product: "beta tubulin" }, 0);
  assert.deepEqual(r.product, { total: 2, genomes: [[0, 1], [1, 1]] });
});

test("related finds the same name in other genomes only", () => {
  const r = related(index, { name: "a1", product: "beta tubulin" }, 0);
  assert.deepEqual(r.name, { total: 1, genomes: [[1, 1]] });
});

test("related is exact and case-sensitive, and ignores empty products", () => {
  assert.equal(related(index, { name: "c1", product: "Beta tubulin" }, 2).product, null);
  assert.equal(related(index, { name: "c2", product: "" }, 2).product, null);
});

test("exactQuery builds an anchored regex term and escapes it for the query grammar", () => {
  assert.equal(exactQuery("product", "beta tubulin"), "product:/^beta tubulin$/");
  assert.equal(exactQuery("product", "a.b (x)/y [z]"), "product:/^a\\.b \\(x\\)\\/y \\[z\\]$/");
});
