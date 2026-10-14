// Ordering of the result table; empty values go last whichever the direction.
import { geneLength } from "./links.js?v=11";

const collator = new Intl.Collator("en", { numeric: true, sensitivity: "base" });

function value(gene, key) {
  if (key === "length") return geneLength(gene);
  if (key === "location") return gene.seqid === undefined ? "" : gene.seqid;
  return gene[key] === undefined || gene[key] === null ? "" : gene[key];
}

function compare(a, b, key) {
  const x = value(a, key);
  const y = value(b, key);
  if (key === "length") return x - y;
  const order = collator.compare(String(x), String(y));
  return order !== 0 || key !== "location" ? order : a.start - b.start;
}

export function sortGenes(genes, key, dir) {
  const sign = dir === "desc" ? -1 : 1;
  const empty = (g) => value(g, key) === "";
  return genes
    .map((gene, index) => ({ gene, index }))
    .sort((a, b) => empty(a.gene) - empty(b.gene) || (empty(a.gene) ? 0 : sign * compare(a.gene, b.gene, key)) || a.index - b.index)
    .map((x) => x.gene);
}
