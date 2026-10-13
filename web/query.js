// Query grammar shared with leishgene/search.py; tests/query_cases.json pins both.
const FIELDS = ["id", "name", "product", "type", "species", "genome", "ec", "go", "dbxref"];
const LIST_FIELDS = new Set(["ec", "go", "dbxref"]);
const SHARD_FIELDS = new Set(["type", "ec", "go", "dbxref"]);
const BARE_FIELDS = ["id", "name", "product", "ec", "go", "dbxref"];
const TOKEN = /(?:(\w+):)?(?:"([^"]*)"|\/((?:\\.|[^/\\])*)\/|(\S+))/g;

export class QueryError extends Error {}

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function termPattern(quoted, regex, plain) {
  if (regex !== undefined) {
    try {
      return new RegExp(regex, "i");
    } catch (e) {
      throw new QueryError(`invalid regular expression /${regex}/: ${e.message}`);
    }
  }
  const text = quoted !== undefined ? quoted : plain;
  return new RegExp(text.split("*").map(escapeRe).join(".*"), "i");
}

function values(gene, field) {
  const v = gene[field];
  if (v === undefined || v === null) return [];
  return LIST_FIELDS.has(field) ? v.map(String) : [String(v)];
}

function bareValues(gene) {
  const out = [];
  for (const f of BARE_FIELDS) out.push(...values(gene, f));
  out.push(...Object.values(gene.attrs || {}).map(String));
  return out;
}

export function parseQuery(text) {
  const terms = [];
  for (const m of text.matchAll(TOKEN)) {
    let [, field, quoted, regex, plain] = m;
    if (field !== undefined && !FIELDS.includes(field.toLowerCase())) {
      const rest = plain !== undefined ? plain : quoted !== undefined ? quoted : `/${regex}/`;
      plain = `${field}:${rest}`;
      quoted = regex = undefined;
      field = undefined;
    }
    terms.push({
      field: field ? field.toLowerCase() : null,
      raw: plain !== undefined ? plain : quoted !== undefined ? quoted : regex,
      pattern: termPattern(quoted, regex, plain),
    });
  }
  return {
    terms,
    matches(gene) {
      return terms.every(({ field, pattern }) => (field === null ? bareValues(gene) : values(gene, field)).some((v) => pattern.test(v)));
    },
  };
}

// names.json only holds id/name/product: anything else needs the per-genome shards. A bare term with a colon
// (GeneID:123, old_locus_tag values) is an annotation ID, which only the shards carry.
export function needsShards(query, allFields) {
  return allFields || query.terms.some((t) => (t.field === null ? t.raw.includes(":") : SHARD_FIELDS.has(t.field)));
}
