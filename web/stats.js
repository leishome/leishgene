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
