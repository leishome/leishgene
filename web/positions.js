// Layout of matches along the sequences of one genome (for the position plot).
const collator = new Intl.Collator("en", { numeric: true, sensitivity: "base" });

// rows: one per sequence with its length and a tick per gene (fraction of the length, at the gene midpoint);
// scale is the longest sequence, so that the rows share one scale; hidden counts the shorter sequences left out.
export function layoutPositions(genes, seqlens, maxRows) {
  const bySeq = new Map();
  for (const g of genes) {
    if (!bySeq.has(g.seqid)) bySeq.set(g.seqid, []);
    bySeq.get(g.seqid).push(g);
  }
  const rows = [...bySeq].map(([seqid, list]) => {
    const length = Math.max(seqlens[seqid] || 0, ...list.map((g) => g.end));
    return { seqid, length, ticks: list.map((g) => ({ frac: (g.start + g.end) / 2 / length, id: g.id, start: g.start, end: g.end })) };
  });
  const kept = rows.sort((a, b) => b.length - a.length || collator.compare(a.seqid, b.seqid)).slice(0, maxRows);
  kept.sort((a, b) => collator.compare(a.seqid, b.seqid));
  return { rows: kept, scale: Math.max(0, ...kept.map((r) => r.length)), hidden: rows.length - kept.length };
}

// Round axis marks (1, 2 or 5 x a power of ten), at most 8 of them.
export function axisTicks(max) {
  for (let power = 1; ; power *= 10) {
    for (const m of [1, 2, 5]) {
      const step = m * power;
      if (Math.floor(max / step) + 1 <= 8) return { step, marks: Array.from({ length: Math.floor(max / step) + 1 }, (_, i) => i * step) };
    }
  }
}
