import test from "node:test";
import assert from "node:assert/strict";
import { geneLinks, geneLength, refUrl, uniprotAccessions } from "../links.js";

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
    { label: "NCBI Gene 1", url: "https://www.ncbi.nlm.nih.gov/gene/1" },
  ]);
});

test("geneLinks falls back to NCBI_GP, and has nothing for a gene without protein", () => {
  assert.deepEqual(geneLinks({ dbxref: ["NCBI_GP:CBZ11804.1"], attrs: {} }), [
    { label: "UniParc", url: "https://www.uniprot.org/uniparc?query=CBZ11804.1" },
  ]);
  assert.deepEqual(geneLinks({ dbxref: [], attrs: {} }), []);
});

test("refUrl maps known database references and leaves the others plain", () => {
  assert.equal(refUrl("dbxref", "GeneID:5651"), "https://www.ncbi.nlm.nih.gov/gene/5651");
  assert.equal(refUrl("dbxref", "InterPro:IPR000719"), "https://www.ebi.ac.uk/interpro/entry/InterPro/IPR000719/");
  assert.equal(refUrl("dbxref", "UniProtKB/Swiss-Prot:P12345"), "https://www.uniprot.org/uniprotkb/P12345");
  assert.equal(refUrl("dbxref", "PFAM:PF00069"), "https://www.ebi.ac.uk/interpro/entry/pfam/PF00069/");
  assert.equal(refUrl("dbxref", "PDB:1ABC"), "https://www.rcsb.org/structure/1ABC");
  assert.equal(refUrl("dbxref", "GenBank:CBZ1.1"), null);
  assert.equal(refUrl("go", "GO:0004672"), "https://www.ebi.ac.uk/QuickGO/term/GO:0004672");
  assert.equal(refUrl("ec", "2.7.11.1"), "https://enzyme.expasy.org/EC/2.7.11.1");
  assert.equal(refUrl("go", "free text"), null);
});
