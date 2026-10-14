import { download, fileName, toBed, toDelimited } from "./export.js?v=10";
import { binLengths, countBy, withOther } from "./stats.js?v=10";
import { detailSections } from "./detail.js?v=10";
import { highlight } from "./highlight.js?v=10";
import { geneLength, geneLinks } from "./links.js?v=10";
import { needsShards, parseQuery, QueryError } from "./query.js?v=10";
import { createShardCache } from "./shards.js?v=10";
import { sortGenes } from "./sort.js?v=10";
import { searchParams } from "./url.js?v=10";

const $ = (s) => document.querySelector(s);
const LIMIT = 100;

let manifest = [];
let names = [];
let run = 0;
let getMatches = null; // resolves every match of the current search (the table shows only `shown` rows)
let currentQuery = null;
let currentTotal = 0;
let currentNamesOnly = false;
let shown = LIMIT;
const sort = { key: null, dir: "asc" };

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response.json();
}

const loadShard = createShardCache(async (index) => {
  const entry = manifest[index];
  const genes = await getJson(`data/${entry.genome}.json`);
  for (const g of genes) Object.assign(g, { species: entry.species || "", strain: entry.strain || "", aliases: entry.aliases || [] });
  return genes;
});

const genomeLabel = (id) => {
  const entry = manifest.find((m) => m.genome === id);
  return entry && entry.strain ? `${id} (${entry.strain})` : id;
};

// One horizontal bar chart: single series, so no legend; each bar adds a filter to the query when clicked.
function barChart(title, entries, maxBars, labelOf, filterOf, noun = "matches") {
  const { shown, other } = withOther(entries, maxBars);
  const max = Math.max(...entries.map((e) => e[1]));
  const box = document.createElement("div");
  box.className = "chart";
  const h = document.createElement("h3");
  h.textContent = title;
  box.append(h);
  const row = (label, count, tip, filter) => {
    const el = document.createElement(filter ? "button" : "div");
    el.className = "bar-row";
    if (filter) {
      el.type = "button";
      el.addEventListener("click", () => applyFilter(filter));
    }
    el.title = tip;
    const name = document.createElement("span");
    name.className = "bar-label";
    name.textContent = label;
    const track = document.createElement("span");
    track.className = "bar-track";
    const bar = document.createElement("span");
    bar.className = "hbar";
    bar.style.width = `${Math.max((count / max) * 100, 0.5)}%`;
    if (filter !== undefined) track.append(bar); // the folded "others" row has no bar: its sum would dwarf the real ones
    const value = document.createElement("span");
    value.className = "bar-value";
    value.textContent = count.toLocaleString("en");
    el.append(name, track, value);
    box.append(el);
  };
  for (const [key, count] of shown) row(labelOf(key), count, `${labelOf(key)}: ${count.toLocaleString("en")} ${noun}` + (filterOf ? " (click to filter)" : ""), filterOf ? filterOf(key) : null);
  if (other) row(`${other.groups} others`, other.count, `${other.groups} more: ${other.count.toLocaleString("en")} ${noun}`);
  return box;
}

function applyFilter(filter) {
  const q = $("#q");
  q.value = `${q.value.trim()} ${filter}`.trim();
  onQuery();
}

const quoteValue = (v) => (/\s/.test(v) ? `"${v}"` : v);

const typeFilter = (t) => (t === "unknown" ? null : `type:${quoteValue(t)}`);
const genomeFilter = (id) => `genome:${quoteValue(id)}`;

function renderCharts(stats, total) {
  const box = $("#charts");
  box.replaceChildren();
  box.hidden = total === 0 || !stats;
  if (box.hidden) return;
  box.append(barChart("Matches per genome", stats.genomes, 12, genomeLabel, genomeFilter));
  if (stats.types) box.append(barChart("Matches by type", stats.types, 10, (t) => t, typeFilter));
  if (stats.lengths) box.append(barChart("Gene length of the matches", stats.lengths, 6, (label) => label, null));
}

// Before any search: the whole database, from the manifest. A click on a genome bar searches that genome.
function showOverview() {
  const ok = manifest.filter((m) => m.status === "ok");
  const box = $("#charts");
  box.replaceChildren();
  if (ok.length === 0) {
    box.hidden = true;
    return;
  }
  const perGenome = ok.map((m) => [m.genome, m.genes]).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
  box.append(barChart("Genes per genome", perGenome, 12, genomeLabel, genomeFilter, "genes"));
  const types = new Map();
  for (const m of ok) for (const [t, n] of Object.entries(m.types || {})) types.set(t, (types.get(t) || 0) + n);
  const byType = [...types].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
  if (byType.length > 0) box.append(barChart("Genes by type", byType, 10, (t) => t, typeFilter, "genes"));
  box.hidden = false;
}

// Expands or folds the row that lists EC, GO, Dbxref and attributes of a gene.
function toggleDetail(tr, gene) {
  const next = tr.nextElementSibling;
  if (next && next.classList.contains("detail")) {
    next.remove();
    tr.setAttribute("aria-expanded", "false");
    return;
  }
  const row = document.createElement("tr");
  row.className = "detail";
  const cell = document.createElement("td");
  cell.colSpan = tr.children.length;
  const sections = detailSections(gene);
  if (sections.length === 0) cell.textContent = "No further annotation for this gene.";
  for (const { label, items } of sections) {
    const line = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = `${label}: `;
    line.append(title);
    items.forEach((item, i) => {
      const el = item.url ? document.createElement("a") : document.createElement("span");
      el.textContent = item.text;
      if (item.url) {
        el.href = item.url;
        el.target = "_blank";
        el.rel = "noopener";
      }
      line.append(el, i < items.length - 1 ? ", " : "");
    });
    cell.append(line);
  }
  row.append(cell);
  tr.after(row);
  tr.setAttribute("aria-expanded", "true");
}

// Highlighted text for a table column: only the query terms that can match that column count.
const COLUMN_FIELDS = { genome: ["genome"], species: ["species"], strain: ["genome"], id: ["id", "name"], product: ["product"] };

function cellContent(text, column) {
  const fields = COLUMN_FIELDS[column];
  const patterns = currentQuery && fields ? currentQuery.terms.filter((t) => t.field === null || fields.includes(t.field)).map((t) => t.pattern) : [];
  const nodes = [];
  for (const part of highlight(text, patterns)) {
    if (part.hit) {
      const mark = document.createElement("mark");
      mark.textContent = part.text;
      nodes.push(mark);
    } else nodes.push(part.text);
  }
  return nodes;
}

function fillTable(rows) {
  const body = $("#results tbody");
  body.replaceChildren();
  const columns = ["genome", "species", "strain", "location", "length", "strand", "id", "type", "product"];
  for (const g of rows) {
    const tr = document.createElement("tr");
    const cells = [
      g.genome,
      g.species || "",
      g.strain || "",
      g.seqid !== undefined ? `${g.seqid}:${g.start}-${g.end}` : "",
      geneLength(g) === "" ? "" : `${geneLength(g).toLocaleString("en")} bp`,
      g.strand || "",
      g.id,
      g.type || "",
      g.product || "",
    ];
    cells.forEach((text, i) => {
      const td = document.createElement("td");
      if (i === 3 || i === 4 || i === 6) td.className = "mono";
      td.append(...cellContent(text, columns[i]));
      tr.append(td);
    });
    const links = document.createElement("td");
    for (const { label, url } of geneLinks(g)) {
      const a = document.createElement("a");
      a.href = url;
      a.textContent = label;
      a.target = "_blank";
      a.rel = "noopener";
      links.append(a, document.createElement("br"));
    }
    tr.append(links);
    tr.className = "clickable";
    tr.tabIndex = 0;
    tr.setAttribute("aria-expanded", "false");
    tr.addEventListener("click", (e) => {
      if (!e.target.closest("a")) toggleDetail(tr, g);
    });
    tr.addEventListener("keydown", (e) => {
      if (e.target === tr && (e.key === "Enter" || e.key === " ")) {
        e.preventDefault();
        toggleDetail(tr, g);
      }
    });
    body.append(tr);
  }
  $("#results").hidden = rows.length === 0;
  $("#more").hidden = currentTotal <= rows.length;
  $("#more").textContent = `Show ${Math.min(LIMIT, currentTotal - rows.length)} more`;
  let status = currentTotal > rows.length ? `${currentTotal} matches, showing ${rows.length}` : `${currentTotal} match(es)`;
  if (currentTotal === 0 && currentNamesOnly) status += " in id/name/product; tick 'search all annotation fields' to search EC, GO, Dbxref and attributes";
  $("#status").textContent = status;
}

function render(rows, total, namesOnly, stats) {
  currentTotal = total;
  currentNamesOnly = namesOnly;
  fillTable(rows);
  renderCharts(stats, total);
  for (const b of document.querySelectorAll(".export")) b.disabled = total === 0;
}

// Re-draws the table after a change of order or of the number of rows; a names-only search loads its genomes first.
async function rerender() {
  if (!getMatches) return;
  const id = run;
  $("#status").textContent = "Loading…";
  const genes = await getMatches();
  if (id !== run) return;
  fillTable((sort.key ? sortGenes(genes, sort.key, sort.dir) : genes).slice(0, shown));
}

function setSort(key) {
  if (sort.key === key && sort.dir === "asc") sort.dir = "desc";
  else if (sort.key === key) sort.key = null;
  else Object.assign(sort, { key, dir: "asc" });
  for (const th of document.querySelectorAll("th[data-sort]")) {
    th.setAttribute("aria-sort", th.dataset.sort === sort.key ? (sort.dir === "asc" ? "ascending" : "descending") : "none");
  }
  rerender().catch((e) => ($("#status").textContent = `Could not sort: ${e.message}`));
}

async function search() {
  const id = ++run;
  const text = $("#q").value;
  const error = $("#error");
  error.hidden = true;
  let query;
  try {
    query = parseQuery(text);
  } catch (e) {
    if (!(e instanceof QueryError)) throw e;
    error.textContent = e.message;
    error.hidden = false;
    $("#results").hidden = true;
    $("#more").hidden = true;
    clearExport();
    return;
  }
  if (query.terms.length === 0) {
    $("#results").hidden = true;
    $("#more").hidden = true;
    clearExport();
    showOverview();
    $("#status").textContent = `${names.length} genes in ${manifest.filter((m) => m.status === "ok").length} genomes`;
    return;
  }
  currentQuery = query;
  shown = LIMIT;
  Object.assign(sort, { key: null, dir: "asc" });
  for (const th of document.querySelectorAll("th[data-sort]")) th.setAttribute("aria-sort", "none");
  const wantShards = needsShards(query, $("#all").checked);
  let hits = [];
  let stats = null;
  const matched = [];
  let total = 0;
  if (wantShards) {
    const ok = manifest.map((m, i) => i).filter((i) => manifest[i].status === "ok");
    let done = 0;
    for (const i of ok) {
      $("#status").textContent = `Loading genome data… ${done}/${ok.length}`;
      const genes = await loadShard(i);
      if (id !== run) return;
      done++;
      for (const g of genes) {
        if (query.matches(g)) {
          total++;
          matched.push(g);
        }
      }
    }
    hits = matched.slice(0, LIMIT);
    stats = { genomes: countBy(matched, (g) => g.genome), types: countBy(matched, (g) => g.type), lengths: binLengths(matched) };
    getMatches = async () => matched;
  } else {
    const all = [];
    for (const [gi, gid, name, product] of names) {
      const entry = manifest[gi];
      if (query.matches({ genome: entry.genome, species: entry.species || "", strain: entry.strain || "", aliases: entry.aliases || [], id: gid, name, product })) {
        all.push({ gi, id: gid });
      }
    }
    total = all.length;
    stats = { genomes: countBy(all, (r) => manifest[r.gi].genome), types: null };
    const rows = all.slice(0, LIMIT);
    // names.json carries no coordinates: fetch only the shards of the genomes that were hit
    const needed = [...new Set(rows.map((r) => r.gi))];
    for (const [n, gi] of needed.entries()) {
      $("#status").textContent = `Loading ${manifest[gi].genome} (${n + 1}/${needed.length})…`;
      await loadShard(gi);
      if (id !== run) return;
    }
    const byId = new Map();
    for (const gi of needed) for (const g of await loadShard(gi)) byId.set(`${gi}\t${g.id}`, g);
    hits = rows.map((r) => byId.get(`${r.gi}\t${r.id}`)).filter(Boolean);
    getMatches = async () => {
      const genes = new Map();
      for (const gi of new Set(all.map((r) => r.gi))) for (const g of await loadShard(gi)) genes.set(`${gi}\t${g.id}`, g);
      return all.map((r) => genes.get(`${r.gi}\t${r.id}`)).filter(Boolean);
    };
  }
  if (id === run) render(hits, total, !wantShards, stats);
}

function clearExport() {
  getMatches = null;
  $("#charts").hidden = true;
  for (const b of document.querySelectorAll(".export")) b.disabled = true;
}

async function exportTable(sep, ext) {
  if (!getMatches) return;
  const status = $("#status").textContent;
  $("#status").textContent = "Preparing export…";
  try {
    const genes = await getMatches();
    download(ext === "bed" ? toBed(genes) : toDelimited(genes, sep), fileName($("#export-name").value, $("#q").value, ext), "text/plain");
  } finally {
    $("#status").textContent = status;
  }
}

async function onQuery() {
  history.replaceState(null, "", `${location.pathname}${searchParams(location.search, $("#q").value, $("#all").checked)}${location.hash}`);
  try {
    await search();
  } catch (e) {
    $("#results").hidden = true;
    clearExport();
    $("#error").textContent = `Search failed: ${e.message}`;
    $("#error").hidden = false;
    $("#status").textContent = "";
  }
}

async function init() {
  try {
    [manifest, names] = await Promise.all([getJson("data/manifest.json"), getJson("data/names.json")]);
  } catch (e) {
    $("#status").textContent = `Could not load the index: ${e.message}`;
    return;
  }
  const missing = manifest.filter((m) => m.status !== "ok").map((m) => m.genome);
  $("#missing").textContent = missing.length ? `Not searchable (no GFF, or a GFF without genes): ${missing.join(", ")}` : "";
  $("#status").textContent = `${names.length} genes in ${manifest.length - missing.length} genomes`;
  let timer;
  $("#q").addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(onQuery, 150);
  });
  $("#all").addEventListener("change", onQuery);
  $("#export-tsv").addEventListener("click", () => exportTable("\t", "tsv"));
  $("#export-csv").addEventListener("click", () => exportTable(",", "csv"));
  $("#export-bed").addEventListener("click", () => exportTable("\t", "bed"));
  $("#more").addEventListener("click", () => {
    shown += LIMIT;
    rerender().catch((e) => ($("#status").textContent = `Could not load more rows: ${e.message}`));
  });
  for (const th of document.querySelectorAll("th[data-sort]")) th.addEventListener("click", () => setSort(th.dataset.sort));
  const params = new URLSearchParams(location.search);
  const initial = params.get("q");
  if (initial) {
    $("#q").value = initial;
    $("#all").checked = params.get("all") === "1";
    onQuery();
  } else {
    showOverview();
  }
}

$("#theme").addEventListener("click", () => {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
});
init();
