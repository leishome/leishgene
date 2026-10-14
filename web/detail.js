// Fields of a gene that the table has no room for: EC, GO, Dbxref and the remaining GFF attributes.
import { refUrl } from "./links.js?v=10";

export function detailSections(gene) {
  const listed = (label, kind, values) => ({ label, items: (values || []).map((text) => ({ text, url: refUrl(kind, text) })) });
  const attrs = Object.entries(gene.attrs || {}).map(([k, v]) => ({ text: `${k}=${v}`, url: null }));
  return [listed("EC", "ec", gene.ec), listed("GO", "go", gene.go), listed("Dbxref", "dbxref", gene.dbxref), { label: "Attributes", items: attrs }].filter(
    (section) => section.items.length > 0
  );
}
