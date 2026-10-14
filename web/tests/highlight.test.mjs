import test from "node:test";
import assert from "node:assert/strict";
import { highlight } from "../highlight.js";

const re = (s) => new RegExp(s, "i");

test("highlight splits text into plain and matched segments", () => {
  assert.deepEqual(highlight("putative protein kinase", [re("kinase")]), [
    { text: "putative protein ", hit: false },
    { text: "kinase", hit: true },
  ]);
});

test("highlight merges overlapping and adjacent matches of several patterns", () => {
  assert.deepEqual(highlight("abcabc", [re("ab"), re("bc")]), [{ text: "abcabc", hit: true }]);
  assert.deepEqual(highlight("a-b-a", [re("a")]), [{ text: "a", hit: true }, { text: "-b-", hit: false }, { text: "a", hit: true }]);
});

test("highlight returns the text untouched without patterns or matches", () => {
  assert.deepEqual(highlight("abc", []), [{ text: "abc", hit: false }]);
  assert.deepEqual(highlight("abc", [re("z")]), [{ text: "abc", hit: false }]);
  assert.deepEqual(highlight("", [re("a")]), []);
});

test("highlight ignores patterns that match the empty string", () => {
  assert.deepEqual(highlight("abc", [re("x*")]), [{ text: "abc", hit: false }]);
  assert.deepEqual(highlight("abc", [re("b*")]), [{ text: "a", hit: false }, { text: "b", hit: true }, { text: "c", hit: false }]);
});
