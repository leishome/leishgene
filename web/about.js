// "What is included": built from data/manifest.json, so it always describes the data the site was built with.
const REASONS = {
  missing: "its GFF was not in the local cache when the site was built",
  empty: "its GFF has no genes",
};

export function summarize(manifest) {
  const ok = manifest.filter((m) => m.status === "ok");
  return {
    searchable: ok.length,
    genes: ok.reduce((sum, m) => sum + m.genes, 0),
    localOverrides: ok.filter((m) => m.source === "local override").map((m) => m.genome),
    notSearchable: manifest.filter((m) => m.status !== "ok").map((m) => ({ genome: m.genome, reason: REASONS[m.status] || m.status })),
  };
}

const el = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};

async function main() {
  const out = document.querySelector("#genomes");
  let manifest;
  try {
    const response = await fetch("data/manifest.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    manifest = await response.json();
  } catch (e) {
    out.textContent = `Could not load the genome list: ${e.message}`;
    return;
  }
  const s = summarize(manifest);
  document.querySelector("#summary").textContent = `${s.searchable} genomes and ${s.genes.toLocaleString("en")} genes are searchable.`;
  const table = el("table", undefined, "dt");
  const head = el("tr");
  for (const h of ["genome", "species", "strain", "aliases", "annotation file", "source", "genes"]) head.append(el("th", h));
  const thead = el("thead");
  thead.append(head);
  table.append(thead);
  const body = el("tbody");
  for (const m of manifest.filter((x) => x.status === "ok")) {
    const tr = el("tr");
    const cells = [m.genome, m.species || "", m.strain || "", (m.aliases || []).join(", "), m.gff || "", m.source || "", m.genes.toLocaleString("en")];
    for (const [i, text] of cells.entries()) tr.append(el("td", text, i === 0 || i === 4 ? "mono" : undefined));
    body.append(tr);
  }
  table.append(body);
  out.replaceChildren(table);
  const notes = document.querySelector("#left-out");
  for (const { genome, reason } of s.notSearchable) notes.append(el("li", `${genome}: ${reason}.`));
  notes.hidden = s.notSearchable.length === 0;
  document.querySelector("#left-out-title").hidden = notes.hidden;
}

if (typeof document !== "undefined") main();
