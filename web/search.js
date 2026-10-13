import { parseQuery, QueryError } from "./query.js";

const $ = (s) => document.querySelector(s);
const SHARD_FIELDS = new Set(["type", "ec", "go", "dbxref"]);
const LIMIT = 100;

let manifest = [];
let names = [];
const shards = new Map(); // genome index -> gene list
let run = 0;

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response.json();
}

async function loadShard(index) {
  if (!shards.has(index)) {
    const entry = manifest[index];
    const genes = await getJson(`data/${entry.genome}.json`);
    for (const g of genes) g.species = entry.species || "";
    shards.set(index, genes);
  }
  return shards.get(index);
}

function render(rows, total) {
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
  $("#status").textContent = total > rows.length ? `${total} matches, showing ${rows.length}` : `${total} match(es)`;
}

async function onQuery() {
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
    return;
  }
  if (query.terms.length === 0) {
    $("#results").hidden = true;
    $("#status").textContent = `${names.length} genes in ${manifest.filter((m) => m.status === "ok").length} genomes`;
    return;
  }
  const needsShards = $("#all").checked || query.terms.some((t) => SHARD_FIELDS.has(t.field));
  let hits = [];
  let total = 0;
  if (needsShards) {
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
          if (hits.length < LIMIT) hits.push(g);
        }
      }
    }
  } else {
    const rows = [];
    for (const [gi, gid, name, product] of names) {
      const entry = manifest[gi];
      if (query.matches({ genome: entry.genome, species: entry.species || "", id: gid, name, product })) {
        total++;
        if (rows.length < LIMIT) rows.push({ gi, id: gid, name });
      }
    }
    // names.json carries no coordinates: fetch only the shards of the genomes that were hit
    const needed = [...new Set(rows.map((r) => r.gi))];
    for (const [n, gi] of needed.entries()) {
      $("#status").textContent = `Loading ${manifest[gi].genome} (${n + 1}/${needed.length})…`;
      await loadShard(gi);
      if (id !== run) return;
    }
    const byId = new Map();
    for (const gi of needed) for (const g of shards.get(gi)) byId.set(`${gi}\t${g.id}`, g);
    hits = rows.map((r) => byId.get(`${r.gi}\t${r.id}`)).filter(Boolean);
  }
  if (id === run) render(hits, total);
}

async function init() {
  try {
    [manifest, names] = await Promise.all([getJson("data/manifest.json"), getJson("data/names.json")]);
  } catch (e) {
    $("#status").textContent = `Could not load the index: ${e.message}`;
    return;
  }
  const missing = manifest.filter((m) => m.status !== "ok").map((m) => m.genome);
  $("#missing").textContent = missing.length ? `Not searchable (no GFF available): ${missing.join(", ")}` : "";
  $("#status").textContent = `${names.length} genes in ${manifest.length - missing.length} genomes`;
  let timer;
  $("#q").addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(onQuery, 150);
  });
  $("#all").addEventListener("change", onQuery);
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
