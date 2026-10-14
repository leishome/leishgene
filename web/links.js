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

const GENE_ID = "GeneID:";

// Link for a database reference, or null when nothing is known about it: kind is "dbxref", "go" or "ec".
export function refUrl(kind, value) {
  if (kind === "go") return /^GO:\d+$/.test(value) ? `https://www.ebi.ac.uk/QuickGO/term/${value}` : null;
  if (kind === "ec") return /^\d+\.(\d+|-)\.(\d+|-)\.(\d+|-)$/.test(value) ? `https://enzyme.expasy.org/EC/${value}` : null;
  const at = value.indexOf(":");
  const db = value.slice(0, at);
  const id = encodeURIComponent(value.slice(at + 1));
  if (at < 1 || !id) return null;
  if (db === "GeneID") return `https://www.ncbi.nlm.nih.gov/gene/${id}`;
  if (db === "InterPro") return `https://www.ebi.ac.uk/interpro/entry/InterPro/${id}/`;
  if (db === "PFAM") return `https://www.ebi.ac.uk/interpro/entry/pfam/${id}/`;
  if (db === "PDB") return `https://www.rcsb.org/structure/${id}`;
  if (db.startsWith("UniProtKB/")) return `${UNIPROT}/uniprotkb/${id}`;
  return null;
}

// UniProt entries from the Dbxref accessions, NCBI Gene from GeneID; UniParc has no accession in the GFFs, so it is a search on the
// protein accession (a UniParc cross-reference).
export function geneLinks(gene) {
  const links = uniprotAccessions(gene).map((acc) => ({ label: `UniProt ${acc}`, url: `${UNIPROT}/uniprotkb/${encodeURIComponent(acc)}` }));
  const protein = proteinAccession(gene);
  if (protein) links.push({ label: "UniParc", url: `${UNIPROT}/uniparc?query=${encodeURIComponent(protein)}` });
  for (const ref of gene.dbxref || []) {
    if (ref.startsWith(GENE_ID)) links.push({ label: `NCBI Gene ${ref.slice(GENE_ID.length)}`, url: refUrl("dbxref", ref) });
  }
  return links;
}
