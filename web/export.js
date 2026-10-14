import { geneLength, uniprotAccessions } from "./links.js?v=11";
// Table export of search hits; same columns and quoting as leishgene/table.py.
export const COLUMNS = ["genome", "species", "strain", "seqid", "start", "end", "length", "strand", "id", "name", "type", "product", "ec", "go", "dbxref", "uniprot"];
const LIST_COLUMNS = new Set(["ec", "go", "dbxref", "uniprot"]);

function cell(gene, column, sep) {
  const v = column === "length" ? geneLength(gene) : column === "uniprot" ? uniprotAccessions(gene) : gene[column];
  let text = v === undefined || v === null ? "" : LIST_COLUMNS.has(column) ? v.join(";") : String(v);
  if (text.includes(sep) || /["\n\r]/.test(text)) text = `"${text.replaceAll('"', '""')}"`;
  return text;
}

export function toDelimited(genes, sep) {
  const lines = [COLUMNS.join(sep), ...genes.map((g) => COLUMNS.map((c) => cell(g, c, sep)).join(sep))];
  return lines.join("\n") + "\n";
}

export function download(text, filename, mime) {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

const sanitise = (text) => text.trim().replace(/[^\w.-]+/g, "_").replace(/^_+|_+$/g, "");

// Download name: the typed one (extension forced to the clicked format), else one derived from the query.
export function fileName(typed, query, ext) {
  const name = sanitise(typed).replace(/\.(tsv|csv|bed)$/i, "");
  return `${name || `leishgene_${sanitise(query).slice(0, 40) || "search"}`}.${ext}`;
}

// BED6: 0-based start, the gene id as name (whitespace becomes "_"), score 0, strand or ".".
export function toBed(genes) {
  return genes.map((g) => `${g.seqid}\t${g.start - 1}\t${g.end}\t${String(g.id).split(/\s+/).join("_")}\t0\t${g.strand || "."}\n`).join("");
}
