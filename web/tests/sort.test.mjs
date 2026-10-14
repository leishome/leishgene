import test from "node:test";
import assert from "node:assert/strict";
import { sortGenes } from "../sort.js";

const g = (id, seqid, start, end, extra = {}) => ({ id, seqid, start, end, genome: "G", ...extra });

test("sortGenes by length is numeric, and does not mutate", () => {
  const genes = [g("a", "c1", 1, 1000), g("b", "c1", 1, 99), g("c", "c1", 1, 10000)];
  assert.deepEqual(sortGenes(genes, "length", "asc").map((x) => x.id), ["b", "a", "c"]);
  assert.deepEqual(sortGenes(genes, "length", "desc").map((x) => x.id), ["c", "a", "b"]);
  assert.deepEqual(genes.map((x) => x.id), ["a", "b", "c"]);
});

test("sortGenes by location orders sequence names naturally, then start", () => {
  const genes = [g("a", "chr10", 5, 9), g("b", "chr2", 50, 90), g("c", "chr2", 7, 9)];
  assert.deepEqual(sortGenes(genes, "location", "asc").map((x) => x.id), ["c", "b", "a"]);
});

test("sortGenes by text is case-insensitive and keeps ties in input order", () => {
  const genes = [g("a", "c", 1, 2, { product: "Kinase" }), g("b", "c", 1, 2, { product: "actin" }), g("c", "c", 1, 2, { product: "kinase" })];
  assert.deepEqual(sortGenes(genes, "product", "asc").map((x) => x.id), ["b", "a", "c"]);
});

test("sortGenes puts empty values last in both directions", () => {
  const genes = [g("a", "c", 1, 2, { type: "" }), g("b", "c", 1, 2, { type: "gene" }), g("c", "c", 1, 2, { type: "tRNA" })];
  assert.deepEqual(sortGenes(genes, "type", "asc").map((x) => x.id), ["b", "c", "a"]);
  assert.deepEqual(sortGenes(genes, "type", "desc").map((x) => x.id), ["c", "b", "a"]);
});
