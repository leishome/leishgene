import test from "node:test";
import assert from "node:assert/strict";
import { detailSections } from "../detail.js";

const gene = {
  id: "g1", name: "g1", product: "kinase",
  ec: ["2.7.11.1"], go: ["GO:0004672"], dbxref: ["GeneID:1", "GenBank:X1"],
  attrs: { locus_tag: "L1", note: "a b" },
};

test("detailSections lists EC, GO, Dbxref and attributes with links where known", () => {
  assert.deepEqual(detailSections(gene), [
    { label: "EC", items: [{ text: "2.7.11.1", url: "https://enzyme.expasy.org/EC/2.7.11.1" }] },
    { label: "GO", items: [{ text: "GO:0004672", url: "https://www.ebi.ac.uk/QuickGO/term/GO:0004672" }] },
    { label: "Dbxref", items: [{ text: "GeneID:1", url: "https://www.ncbi.nlm.nih.gov/gene/1" }, { text: "GenBank:X1", url: null }] },
    { label: "Attributes", items: [{ text: "locus_tag=L1", url: null }, { text: "note=a b", url: null }] },
  ]);
});

test("detailSections skips empty sections", () => {
  assert.deepEqual(detailSections({ ec: [], go: [], dbxref: [], attrs: {} }), []);
  assert.deepEqual(detailSections({}), []);
});
