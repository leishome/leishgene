import test from "node:test";
import assert from "node:assert/strict";
import { geneLinks, geneLength, uniprotAccessions } from "../links.js";

const gene = {
  start: 100, end: 1299,
  dbxref: ["GeneID:1", "UniProtKB/TrEMBL:E9ABZ0", "UniProtKB/Swiss-Prot:P12345", "UniProtKB/TrEMBL:E9ABZ0", "NCBI_GP:CBZ1.1"],
  attrs: { protein_id: "XP_067712555.1" },
};

test("geneLength counts both ends", () => {
  assert.equal(geneLength(gene), 1200);
  assert.equal(geneLength({ start: 5, end: 5 }), 1);
  assert.equal(geneLength({}), "");
});

test("uniprotAccessions reads TrEMBL and Swiss-Prot once each", () => {
  assert.deepEqual(uniprotAccessions(gene), ["E9ABZ0", "P12345"]);
  assert.deepEqual(uniprotAccessions({ dbxref: ["GeneID:1"] }), []);
  assert.deepEqual(uniprotAccessions({}), []);
});

test("geneLinks: UniProt entries and a UniParc search on the protein accession", () => {
  assert.deepEqual(geneLinks(gene), [
    { label: "UniProt E9ABZ0", url: "https://www.uniprot.org/uniprotkb/E9ABZ0" },
    { label: "UniProt P12345", url: "https://www.uniprot.org/uniprotkb/P12345" },
    { label: "UniParc", url: "https://www.uniprot.org/uniparc?query=XP_067712555.1" },
  ]);
});

test("geneLinks falls back to NCBI_GP, and has nothing for a gene without protein", () => {
  assert.deepEqual(geneLinks({ dbxref: ["NCBI_GP:CBZ11804.1"], attrs: {} }), [
    { label: "UniParc", url: "https://www.uniprot.org/uniparc?query=CBZ11804.1" },
  ]);
  assert.deepEqual(geneLinks({ dbxref: [], attrs: {} }), []);
});
