// "The same gene elsewhere": genes of other genomes with the same exact name or product, from names.json.

// [[genome index, id, name, product]] -> {byProduct, byName}: Map(key -> Map(genome index -> count))
export function buildRelatedIndex(names) {
  const byProduct = new Map();
  const byName = new Map();
  const add = (map, key, gi) => {
    if (key === "") return;
    if (!map.has(key)) map.set(key, new Map());
    const counts = map.get(key);
    counts.set(gi, (counts.get(gi) || 0) + 1);
  };
  for (const [gi, , name, product] of names) {
    add(byName, name, gi);
    add(byProduct, product, gi);
  }
  return { byProduct, byName };
}

function others(map, key, gi) {
  const counts = new Map(map.get(key) || []);
  if (counts.has(gi)) counts.set(gi, counts.get(gi) - 1); // the gene itself
  const genomes = [...counts].filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1] || a[0] - b[0]);
  return genomes.length === 0 ? null : { total: genomes.reduce((sum, [, n]) => sum + n, 0), genomes };
}

// What else carries this gene's exact product / name; null when nothing does. gi is the gene's genome index.
export function related(index, gene, gi) {
  return { product: others(index.byProduct, gene.product || "", gi), name: others(index.byName, gene.name || "", gi) };
}

// Query term that matches the value exactly (a regex, escaped for the query grammar).
export function exactQuery(field, value) {
  return `${field}:/^${value.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&")}$/`;
}
