import test from "node:test";
import assert from "node:assert/strict";
import { COLUMNS, toDelimited } from "../export.js";

const gene = {
  genome: "G1", species: "Leishmania donovani", strain: "pasteur", seqid: "c1", start: 5, end: 90, strand: "-", id: "g1", name: "g1",
  type: "gene", product: 'kinase, "putative"\tline', ec: ["2.7.11.1", "2.7.1.1"], go: [], dbxref: ["GeneID:1"],
};

test("columns are fixed", () => {
  assert.deepEqual(COLUMNS, "genome species strain seqid start end length strand id name type product ec go dbxref uniprot".split(" "));
});

test("tsv quotes fields and joins lists", () => {
  const [header, row] = toDelimited([gene], "\t").split("\n");
  assert.equal(header, COLUMNS.join("\t"));
  assert.equal(row, 'G1\tLeishmania donovani\tpasteur\tc1\t5\t90\t86\t-\tg1\tg1\tgene\t"kinase, ""putative""\tline"\t2.7.11.1;2.7.1.1\t\tGeneID:1\t');
});

test("csv quotes commas and missing fields are empty", () => {
  const row = toDelimited([{ id: "x", product: "a,b" }], ",").split("\n")[1];
  assert.equal(row, ',,,,,,,,x,,,"a,b",,,,');
});

import { fileName } from "../export.js";

test("fileName falls back to the query", () => {
  assert.equal(fileName("", "Ld1S kinase", "tsv"), "leishgene_Ld1S_kinase.tsv");
  assert.equal(fileName("   ", "", "csv"), "leishgene_search.csv");
});

test("fileName uses the typed name and the button extension", () => {
  assert.equal(fileName("hits", "kinase", "tsv"), "hits.tsv");
  assert.equal(fileName("hits.csv", "kinase", "tsv"), "hits.tsv");
  assert.equal(fileName("my hits/v2", "kinase", "csv"), "my_hits_v2.csv");
  assert.equal(fileName("v1.2", "kinase", "csv"), "v1.2.csv");
});

test("fileName ignores a name that sanitises to nothing", () => {
  assert.equal(fileName("///", "kinase", "tsv"), "leishgene_kinase.tsv");
});

import { toBed } from "../export.js";

test("toBed writes 0-based starts, the id as name and a dot for unknown strand", () => {
  const genes = [{ seqid: "c1", start: 5, end: 90, id: "g 1", strand: "-" }, { seqid: "c2", start: 1, end: 2, id: "g2" }];
  assert.equal(toBed(genes), "c1\t4\t90\tg_1\t0\t-\nc2\t0\t2\tg2\t0\t.\n");
});

test("fileName replaces a .bed extension too", () => {
  assert.equal(fileName("hits.bed", "k", "tsv"), "hits.tsv");
  assert.equal(fileName("hits", "k", "bed"), "hits.bed");
});
