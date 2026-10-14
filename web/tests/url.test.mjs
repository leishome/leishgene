import test from "node:test";
import assert from "node:assert/strict";
import { searchParams } from "../url.js";

test("searchParams writes q and all, keeping other parameters", () => {
  assert.equal(searchParams("", "Ld1S kinase", false), "?q=Ld1S+kinase");
  assert.equal(searchParams("?q=old&all=1", "x", true), "?q=x&all=1");
  assert.equal(searchParams("?q=old&all=1", "x", false), "?q=x");
  assert.equal(searchParams("?debug=1", "go:GO:0004672", false), "?debug=1&q=go%3AGO%3A0004672");
});

test("searchParams clears q for an empty query", () => {
  assert.equal(searchParams("?q=old&all=1", "  ", false), "");
});
