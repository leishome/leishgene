import test from "node:test";
import assert from "node:assert/strict";
import { axisTicks, layoutPositions } from "../positions.js";

const gene = (id, seqid, start, end) => ({ id, seqid, start, end });

test("layoutPositions orders sequences naturally, scales by the longest and places ticks by midpoint", () => {
  const genes = [gene("a", "chr10", 100, 300), gene("b", "chr2", 500, 700), gene("c", "chr2", 0, 100)];
  const out = layoutPositions(genes, { chr2: 1000, chr10: 2000 }, 40);
  assert.equal(out.scale, 2000);
  assert.deepEqual(out.rows.map((r) => [r.seqid, r.length, r.ticks.length]), [["chr2", 1000, 2], ["chr10", 2000, 1]]);
  assert.deepEqual(out.rows[0].ticks.map((t) => t.frac), [0.6, 0.05]);
  assert.equal(out.hidden, 0);
});

test("layoutPositions falls back to the last gene end, keeps the longest rows, and counts the hidden ones", () => {
  const genes = [gene("a", "s1", 1, 50), gene("b", "s2", 1, 500), gene("c", "s3", 1, 200)];
  const out = layoutPositions(genes, {}, 2);
  assert.deepEqual(out.rows.map((r) => r.seqid), ["s2", "s3"]);
  assert.equal(out.hidden, 1);
  assert.equal(out.rows[0].length, 500);
});

test("axisTicks picks a round step with at most 8 marks", () => {
  assert.deepEqual(axisTicks(2_500_000), { step: 500_000, marks: [0, 500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000] });
  assert.equal(axisTicks(40_000).step, 10_000);
  assert.ok(axisTicks(33_000_000).marks.length <= 8);
});
