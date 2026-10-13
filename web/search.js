import { download, toDelimited } from "./export.js";
import { needsShards, parseQuery, QueryError } from "./query.js";
import { createShardCache } from "./shards.js";

const $ = (s) => document.querySelector(s);
const LIMIT = 100;

let manifest = [];
let names = [];
let run = 0;
let getMatches = null; // resolves every match of the current search (the table shows only LIMIT rows)

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

function render(rows, total, namesOnly) {
  const body = $("#results tbody");
  body.replaceChildren();
  for (const g of rows) {
    const tr = document.createElement("tr");
    const cells = [
      g.genome,
      g.species || "",
      g.seqid !== undefined ? `${g.seqid}:${g.start}-${g.end}` : "",
      g.strand || "",
      g.id,
      g.type || "",
      g.product || "",
    ];
    cells.forEach((text, i) => {
      const td = document.createElement("td");
      if (i === 2 || i === 4) td.className = "mono";
      td.textContent = text;
      tr.append(td);
    });
    body.append(tr);
  }
  $("#results").hidden = rows.length === 0;
  for (const b of document.querySelectorAll(".export")) b.disabled = total === 0;
  let status = total > rows.length ? `${total} matches, showing ${rows.length}` : `${total} match(es)`;
  if (total === 0 && namesOnly) status += " in id/name/product; tick 'search all annotation fields' to search EC, GO, Dbxref and attributes";
  $("#status").textContent = status;
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
    clearExport();
    return;
  }
  if (query.terms.length === 0) {
    $("#results").hidden = true;
    clearExport();
    $("#status").textContent = `${names.length} genes in ${manifest.filter((m) => m.status === "ok").length} genomes`;
    return;
  }
  const wantShards = needsShards(query, $("#all").checked);
  let hits = [];
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
  if (id === run) render(hits, total, !wantShards);
}

function clearExport() {
  getMatches = null;
  for (const b of document.querySelectorAll(".export")) b.disabled = true;
}

async function exportTable(sep, ext) {
  if (!getMatches) return;
  const status = $("#status").textContent;
  $("#status").textContent = "Preparing export…";
  try {
    const genes = await getMatches();
    const slug = $("#q").value.trim().replace(/[^\w.-]+/g, "_").slice(0, 40) || "search";
    download(toDelimited(genes, sep), `leishgene_${slug}.${ext}`, "text/plain");
  } finally {
    $("#status").textContent = status;
  }
}

async function onQuery() {
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
  const initial = new URLSearchParams(location.search).get("q");
  if (initial) {
    $("#q").value = initial;
    onQuery();
  }
}

$("#theme").addEventListener("click", () => {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
});
init();
