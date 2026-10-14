import test from "node:test";
import assert from "node:assert/strict";
import { summarize } from "../about.js";

const manifest = [
  { genome: "A", genes: 10, status: "ok", source: "leishref catalog" },
  { genome: "B", genes: 5, status: "ok", source: "local override" },
  { genome: "C", genes: 0, status: "missing", source: "leishref catalog" },
  { genome: "D", genes: 0, status: "empty" },
];

test("summarize counts searchable genomes, genes and the genomes left out", () => {
  assert.deepEqual(summarize(manifest), {
    searchable: 2,
    genes: 15,
    localOverrides: ["B"],
    notSearchable: [{ genome: "C", reason: "its GFF was not in the local cache when the site was built" }, { genome: "D", reason: "its GFF has no genes" }],
  });
});
