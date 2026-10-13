import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseQuery, QueryError } from "../query.js";

const cases = JSON.parse(readFileSync(new URL("../../tests/query_cases.json", import.meta.url)));

for (const c of cases) {
  test(`vector: ${c.query}`, () => {
    if (c.error) {
      assert.throws(() => parseQuery(c.query), QueryError);
    } else {
      assert.equal(parseQuery(c.query).matches(c.gene), c.match);
    }
  });
}

test("empty query has no terms", () => {
  assert.equal(parseQuery("   ").terms.length, 0);
});

test("invalid regex message", () => {
  assert.throws(() => parseQuery("/(/"), /invalid regular expression/);
});
