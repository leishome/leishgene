# leishgene design

Date: 2026-10-13

## Goal

A Python package, `leishgene`, and a static website to find any gene or annotation across Leishmania genomes by pattern, a "super annotation finder". It follows the leishref model: a package with a CLI, plus a static site that searches in the browser with no server.

## Scope

In scope (v1):
- Genomes listed in the leishref catalog that already record a GFF (38 of 162 at the time of writing).
- Parsing GFF3 (NCBI and TriTrypDB dialects), indexing genes, CLI search, and a static site.
- leishref as a dependency, used for genome identity (identifier, species, strain, aliases) and for resolving local GFF paths.

Out of scope (v1):
- Fetching GFFs for genomes that lack one. The index grows as leishref adds GFFs.
- Orthology. Possible later; for now genes are grouped across genomes only by exact `name` or `product` match.
- User-supplied GFFs outside the leishref catalog.

## Package layout

```
leishgene/
  gff.py       parse GFF3 into Feature records
  sources.py   list catalog genomes with a GFF; resolve the local GFF path via leishref
  index.py     build per-genome shards and the global manifest
  search.py    query parsing and matching
  export.py    write site data to web/data/
  cli.py       leishgene build | search PATTERN | export | info
web/           static site: index.html, search.js, style.css
tests/
docs/          Sphinx
```

Data flow: `sources` selects genomes with a GFF, `gff` parses each, `index` writes the shards, `export` publishes them to `web/data/`. The CLI `search` and the website use the same query grammar and fields.

## Data model

- Feature types kept: gene, mRNA, CDS, ncRNA, tRNA, rRNA.
- The search unit is the gene. Child features are folded into their parent gene: transcript IDs, product, EC, GO and Dbxref values.
- Gene record fields: genome, seqid, start, end, strand, type, id, name, product, ec, go, dbxref, attrs (unknown attributes kept verbatim).
- Features without a gene parent (orphan CDS, pseudogenes) are indexed as their own rows.

## Data layout for the site

- `web/data/<genome>.json`: compact gene records for one genome.
- `web/data/manifest.json`: genome metadata (from leishref), gene counts, and status (`ok` or `missing`).
- `web/data/names.json`: only ID, name and product tokens for every gene, for instant first-pass search.
- Shards load lazily, only when a query needs fields beyond names.json (EC, GO, Dbxref, attrs) or the user opens a genome. The first such search is slower, and the UI shows loading progress.

## Search

- Bare terms are AND-ed (multiple words).
- `*` is a glob. `/re/` is a regex.
- `field:value` filters. Fields: `id`, `name`, `product`, `type`, `species`, `genome`, `ec`, `go`.
- Matching is case-insensitive.
- Results show genome, coordinates, strand, product, and a link back to the genome.
- The Python and JavaScript matchers share test vectors in `tests/query_cases.json` so they cannot drift.

## Errors and edge cases

- A catalog genome lists a GFF that is not cached locally: `build` skips it with a warning and records it as `missing` in `manifest.json`. `--strict` makes it fail.
- The parser normalizes the NCBI dialect (`gene-`/`rna-` ID prefixes, `Dbxref`) and the TriTrypDB dialect (`description`, `ebi_biotype`) to the same fields.
- Percent-encoded attribute values are decoded. Gzipped GFFs are accepted.

## Testing

- pytest with small fixture GFFs: one NCBI-style, one TriTrypDB-style, plus edge cases (orphan features, encoding, gz).
- Tests for the parser, gene folding, shard and manifest schema, and the query matcher using the shared vectors.
- A CLI smoke test on the fixtures.
- A CI check that fails when a shard exceeds a size budget.
- Tooling follows the user defaults: poetry, black (line length 120), isort, flake8, pre-commit, Sphinx docs.

## Deployment

A GitHub Actions workflow builds the data and publishes `web/` to GitHub Pages, modelled on leishref's `site.yml`.
