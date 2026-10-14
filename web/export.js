// Table export of search hits; same columns and quoting as leishgene/table.py.
export const COLUMNS = ["genome", "species", "seqid", "start", "end", "strand", "id", "name", "type", "product", "ec", "go", "dbxref"];
const LIST_COLUMNS = new Set(["ec", "go", "dbxref"]);

function cell(gene, column, sep) {
  const v = gene[column];
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
  const name = sanitise(typed).replace(/\.(tsv|csv)$/i, "");
  return `${name || `leishgene_${sanitise(query).slice(0, 40) || "search"}`}.${ext}`;
}
