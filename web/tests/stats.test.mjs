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
