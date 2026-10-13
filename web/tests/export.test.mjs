import test from "node:test";
import assert from "node:assert/strict";
import { COLUMNS, toDelimited } from "../export.js";

const gene = {
  genome: "G1", species: "Leishmania donovani", seqid: "c1", start: 5, end: 90, strand: "-", id: "g1", name: "g1",
  type: "gene", product: 'kinase, "putative"\tline', ec: ["2.7.11.1", "2.7.1.1"], go: [], dbxref: ["GeneID:1"],
};

test("columns are fixed", () => {
  assert.deepEqual(COLUMNS, "genome species seqid start end strand id name type product ec go dbxref".split(" "));
});

test("tsv quotes fields and joins lists", () => {
  const [header, row] = toDelimited([gene], "\t").split("\n");
  assert.equal(header, COLUMNS.join("\t"));
  assert.equal(row, 'G1\tLeishmania donovani\tc1\t5\t90\t-\tg1\tg1\tgene\t"kinase, ""putative""\tline"\t2.7.11.1;2.7.1.1\t\tGeneID:1');
});

test("csv quotes commas and missing fields are empty", () => {
  const row = toDelimited([{ id: "x", product: "a,b" }], ",").split("\n")[1];
  assert.equal(row, ',,,,,,x,,,"a,b",,,');
});
