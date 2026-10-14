// Splits text into plain and matched segments for the query patterns (case-insensitive RegExp objects).
export function highlight(text, patterns) {
  if (text === "") return [];
  const ranges = [];
  for (const pattern of patterns) {
    const re = new RegExp(pattern.source, "gi");
    for (let m = re.exec(text); m !== null; m = re.exec(text)) {
      if (m[0] === "") re.lastIndex++; // a pattern that matches the empty string highlights nothing
      else ranges.push([m.index, m.index + m[0].length]);
    }
  }
  ranges.sort((a, b) => a[0] - b[0]);
  const merged = [];
  for (const [start, end] of ranges) {
    const last = merged[merged.length - 1];
    if (last && start <= last[1]) last[1] = Math.max(last[1], end);
    else merged.push([start, end]);
  }
  const out = [];
  let at = 0;
  for (const [start, end] of merged) {
    if (start > at) out.push({ text: text.slice(at, start), hit: false });
    out.push({ text: text.slice(start, end), hit: true });
    at = end;
  }
  if (at < text.length) out.push({ text: text.slice(at), hit: false });
  return out;
}
