import test from "node:test";
import assert from "node:assert/strict";
import { countBy, withOther } from "../stats.js";

test("countBy counts and sorts by count desc, then key", () => {
  const items = ["b", "a", "b", "c", "a", "b"];
  assert.deepEqual(countBy(items, (x) => x), [["b", 3], ["a", 2], ["c", 1]]);
  assert.deepEqual(countBy(["y", "x"], (x) => x), [["x", 1], ["y", 1]]);
});

test("countBy skips empty keys as 'unknown'", () => {
  assert.deepEqual(countBy([{ t: "" }, { t: "gene" }, {}], (g) => g.t), [["unknown", 2], ["gene", 1]]);
});

test("withOther keeps the top n and folds the rest", () => {
  const entries = [["a", 5], ["b", 4], ["c", 3], ["d", 2]];
  assert.deepEqual(withOther(entries, 2), { shown: [["a", 5], ["b", 4]], other: { count: 5, groups: 2 } });
  assert.deepEqual(withOther(entries, 4), { shown: entries, other: null });
});

import { binLengths } from "../stats.js";

test("binLengths counts gene lengths into fixed bins, keeping empty bins", () => {
  const genes = [{ start: 1, end: 100 }, { start: 1, end: 499 }, { start: 1, end: 500 }, { start: 1, end: 3000 }, { start: 1, end: 20000 }, {}];
  assert.deepEqual(binLengths(genes), [
    ["< 500 bp", 2], ["500 bp – 1 kb", 1], ["1 – 2 kb", 0], ["2 – 4 kb", 1], ["4 – 8 kb", 0], ["≥ 8 kb", 1],
  ]);
});
