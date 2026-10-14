// Counting helpers for the result charts.

// [[key, count]] sorted by count (desc), then key; empty keys count as "unknown".
export function countBy(items, keyFn) {
  const counts = new Map();
  for (const item of items) {
    const key = keyFn(item) || "unknown";
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return [...counts].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
}

// The first n entries, plus how many entries/groups the rest add up to (null when nothing is folded).
export function withOther(entries, n) {
  if (entries.length <= n) return { shown: entries, other: null };
  const rest = entries.slice(n);
  return { shown: entries.slice(0, n), other: { count: rest.reduce((s, e) => s + e[1], 0), groups: rest.length } };
}

const LENGTH_BINS = [
  ["< 500 bp", 500],
  ["500 bp – 1 kb", 1000],
  ["1 – 2 kb", 2000],
  ["2 – 4 kb", 4000],
  ["4 – 8 kb", 8000],
  ["≥ 8 kb", Infinity],
];

// [[label, count]] in length order, empty bins kept so that the shape of the distribution reads at a glance.
export function binLengths(genes) {
  const counts = LENGTH_BINS.map(([label]) => [label, 0]);
  for (const g of genes) {
    if (g.start === undefined || g.end === undefined) continue;
    const length = g.end - g.start + 1;
    counts[LENGTH_BINS.findIndex(([, limit]) => length < limit)][1]++;
  }
  return counts;
}
