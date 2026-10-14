// Derived values for the result table and the exports: gene length and UniProt / UniParc links.
const UNIPROT = "https://www.uniprot.org";

export function geneLength(gene) {
  return gene.start === undefined || gene.end === undefined ? "" : gene.end - gene.start + 1;
}

// Accessions from UniProtKB/TrEMBL:ACC and UniProtKB/Swiss-Prot:ACC Dbxref values, once each.
export function uniprotAccessions(gene) {
  const out = [];
  for (const ref of gene.dbxref || []) {
    if (!ref.startsWith("UniProtKB/")) continue;
    const acc = ref.slice(ref.indexOf(":") + 1);
    if (acc && !out.includes(acc)) out.push(acc);
  }
  return out;
}

function proteinAccession(gene) {
  const id = (gene.attrs || {}).protein_id;
  if (id) return id;
  const gp = (gene.dbxref || []).find((r) => r.startsWith("NCBI_GP:"));
  return gp ? gp.slice("NCBI_GP:".length) : "";
}

// UniProt entries from the Dbxref accessions; UniParc has no accession in the GFFs, so it is a search on the
// protein accession (a UniParc cross-reference).
export function geneLinks(gene) {
  const links = uniprotAccessions(gene).map((acc) => ({ label: `UniProt ${acc}`, url: `${UNIPROT}/uniprotkb/${encodeURIComponent(acc)}` }));
  const protein = proteinAccession(gene);
  if (protein) links.push({ label: "UniParc", url: `${UNIPROT}/uniparc?query=${encodeURIComponent(protein)}` });
  return links;
}
