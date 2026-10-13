# leishgene Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python package and static website that search genes and annotations across the leishref-catalog genomes that have a GFF.

**Architecture:** `leishgene` reads genome identity from `leishref.metadata`, parses cached GFF3 files into gene records (children folded into the parent gene), writes per-genome JSON shards plus a manifest and a names index, and serves them to a client-side JS search page. Python and JS share one query grammar, pinned by shared test vectors.

**Tech Stack:** Python >=3.9, poetry, leishref (dependency), rich-click, pytest, black/isort/flake8, Sphinx; vanilla JS (no build step), GitHub Actions + Pages.

**Spec:** `docs/superpowers/specs/2026-10-13-leishgene-design.md`

## Global Constraints

- Scope: only leishref catalog genomes whose `Genome.gff` is set (38 of 162 today). No GFF fetching, no orthology, no user GFFs.
- Feature types kept: gene, mRNA, CDS, ncRNA, tRNA, rRNA. Search unit is the gene.
- Query grammar: bare terms AND-ed; `*` glob; `/re/` regex; `field:value` with fields `id`, `name`, `product`, `type`, `species`, `genome`, `ec`, `go`; case-insensitive.
- Site data: `web/data/<genome>.json`, `web/data/manifest.json`, `web/data/names.json`.
- Missing cached GFF: skip with warning, record `status: "missing"` in manifest; `--strict` fails instead.
- black line length 120, isort profile black, flake8 ignores E203 E501 W503 E722; poetry; pytest; Sphinx.

## Review Focus

- GFF with no `gene` rows (only mRNA/CDS): CDS/mRNA become their own rows, not silently dropped (Task 2).
- Gene with attribute values containing `;`, `,` or `=` percent-encoded: decoded, not split (Task 2).
- Empty query or only filters: CLI returns all matches for the filter, empty query alone returns nothing with a message (Task 4).
- Invalid regex `/(/`: clear error message, no traceback; the website shows it inline (Tasks 4, 7).
- Genome with zero genes or a missing GFF: manifest entry present, site lists it as unsearchable rather than crashing (Task 3).

---

### Task 1: Project scaffold and leishref source resolution

**Files:**
- Create: `pyproject.toml`, `leishgene/__init__.py`, `leishgene/sources.py`, `tests/test_sources.py`, `.flake8`, `.pre-commit-config.yaml`, `.gitignore`
- Test: `tests/test_sources.py`

**Interfaces:**
- Produces: `GenomeSource` dataclass (`genome_id: str`, `species: str|None`, `strain: str|None`, `aliases: list[str]`, `gff_path: Path|None`, `gff_name: str`); `list_sources(catalog=None, cache_dir=None) -> list[GenomeSource]` returning only genomes with `Genome.gff` set; `gff_path` is `cache_dir/<accession or identifier>/<gff name>` if that file exists, else `None`.

- [ ] **Step 1:** `git init`, then copy the poetry/black/isort/flake8/pre-commit config conventions from `/home/cokelaer/Work/github/leishref` (`pyproject.toml`, `.flake8`, `.pre-commit-config.yaml`); package `leishgene`, dependency `leishref`, script `leishgene = "leishgene.cli:cli"`.
- [ ] **Step 2: Write failing tests** `test_list_sources_only_with_gff`, `test_gff_path_resolved_when_cached`, `test_gff_path_none_when_not_cached` using fake `Genome` objects (from `leishref.metadata`) and `tmp_path` as `cache_dir`. Assert genomes without a gff are excluded; cached file → exact `tmp_path/<accession>/<name>`; not cached → `None`; aliases come from `leishref.metadata.load_aliases()` inverted (accession or identifier → aliases).
- [ ] **Step 3:** Run `pytest tests/test_sources.py -xvs`; expect FAIL (module missing).
- [ ] **Step 4:** Implement `list_sources` per the Interfaces block. Cache key is `genome.accession or genome.identifier` (same rule as `leishref.cli.cache_key`; reimplemented, not imported, to avoid importing the CLI). Default `cache_dir` is `leishref.metadata.CACHE_DIR`.
- [ ] **Step 5:** Run tests; expect PASS. `poetry install` and `poetry run python -c "import leishgene"` succeed.
- [ ] **Step 6:** Commit `feat: scaffold package and leishref source resolution`.

### Task 2: GFF3 parser and gene folding

**Files:**
- Create: `leishgene/gff.py`, `tests/fixtures/ncbi.gff`, `tests/fixtures/tritryp.gff`, `tests/fixtures/edge.gff.gz`, `tests/test_gff.py`
- Test: `tests/test_gff.py`

**Interfaces:**
- Produces: `Gene` dataclass with fields `genome, seqid, start, end, strand, type, id, name, product, ec: list[str], go: list[str], dbxref: list[str], attrs: dict` and `to_dict() -> dict`; `parse_gff(path: Path, genome: str) -> list[Gene]` (accepts `.gz`).

- [ ] **Step 1:** Write small fixtures: NCBI style (`ID=gene-LdBPK_01;Name=...`, `Dbxref=GeneID:123`, mRNA `Parent=gene-...`, CDS with `product=`), TriTrypDB style (`description=`, `ebi_biotype=`, `Ontology_term=GO:...`, `ec_number=`), and an edge file (orphan CDS with no gene row, pseudogene, `product=hypothetical%2C putative%3B x`), gzipped.
- [ ] **Step 2: Write failing tests:** `test_ncbi_gene_folds_children` (gene count, product taken from CDS/mRNA, dbxref list), `test_tritryp_description_and_go_ec`, `test_percent_decoded_not_split` (product equals `hypothetical, putative; x`), `test_orphan_cds_becomes_own_row`, `test_gz_input`, `test_unknown_attrs_kept_verbatim`, `test_comment_and_fasta_section_ignored` (stop at `##FASTA`).
- [ ] **Step 3:** Run; expect FAIL.
- [ ] **Step 4:** Implement `parse_gff`: single pass collecting rows by `ID`, resolve `Parent` links to the gene, merge `product`/`description`, `ec_number`/`EC_number`, `Ontology_term`/`Gene Ontology`, `Dbxref`; `name` falls back to `Name`, `gene`, then `ID` with `gene-` prefix stripped. Orphans become rows with their own type.
- [ ] **Step 5:** Run tests; expect PASS.
- [ ] **Step 6:** Commit `feat: GFF3 parser with gene folding`.

### Task 3: Index builder (shards, manifest, names)

**Files:**
- Create: `leishgene/index.py`, `tests/test_index.py`
- Test: `tests/test_index.py`

**Interfaces:**
- Consumes: `list_sources() -> list[GenomeSource]` (Task 1); `parse_gff(path, genome) -> list[Gene]` (Task 2).
- Produces: `build_index(out_dir: Path, sources: list[GenomeSource], strict: bool = False) -> dict` writing `<genome>.json` (list of `Gene.to_dict()`), `manifest.json` (list of `{genome, species, strain, aliases, genes: int, status: "ok"|"missing"}`) and `names.json` (list of `[genome_index, gene_id, name, product]` rows, with `genome_index` indexing into the manifest order); returns the manifest. `MissingGffError` raised when `strict` and a GFF is not cached.

- [ ] **Step 1: Write failing tests** with `GenomeSource` objects pointing at the Task 2 fixtures: `test_writes_shard_manifest_names`, `test_missing_gff_recorded_not_fatal` (status `missing`, warning logged, no shard), `test_strict_raises_on_missing`, `test_zero_gene_genome_status_ok_count_zero`, `test_names_rows_reference_manifest_index`.
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3:** Implement `build_index`; JSON written compact (`separators=(",", ":")`).
- [ ] **Step 4:** Run; expect PASS.
- [ ] **Step 5:** Commit `feat: shard, manifest and names index builder`.

### Task 4: Query parser and matcher (Python)

**Files:**
- Create: `leishgene/search.py`, `tests/query_cases.json`, `tests/test_search.py`
- Test: `tests/test_search.py`

**Interfaces:**
- Produces: `parse_query(text: str) -> Query` (raises `QueryError` with a readable message on invalid regex); `Query.matches(gene: dict) -> bool`; `search(genes: Iterable[dict], text: str) -> list[dict]`. Shared vectors file `tests/query_cases.json`: list of `{"query": str, "gene": {...}, "match": bool}` (and `{"query":..., "error": true}` for invalid input), consumed by both Python and JS tests.

- [ ] **Step 1:** Write `tests/query_cases.json` with at least: multi-word AND; `kinase*` glob; `/^LdBPK_\d+\.1$/` regex on id; `product:/kinase/`; `type:gene`; `species:donovani`; `ec:2.7.11.1`; `go:0004672`; case-insensitivity; quoted phrase `"protein kinase"`; invalid regex `/(/` → error.
- [ ] **Step 2: Write failing tests:** `test_shared_vectors` (parametrized over the JSON), `test_empty_query_returns_nothing`, `test_filters_only_query_allowed` (e.g. `type:tRNA`), `test_invalid_regex_raises_query_error`.
- [ ] **Step 3:** Run; expect FAIL.
- [ ] **Step 4:** Implement tokenizer (quotes, `field:value`, `/re/`, `*` glob → regex via escape+replace). Bare terms match across `id, name, product, ec, go, dbxref` and attribute values. `species`/`genome` fields use the gene's genome id; `species` resolved by the caller adding a `species` key to each gene dict (see Task 5).
- [ ] **Step 5:** Run; expect PASS.
- [ ] **Step 6:** Commit `feat: query grammar and matcher`.

### Task 5: CLI (`build`, `search`, `export`, `info`)

**Files:**
- Create: `leishgene/cli.py`, `leishgene/export.py`, `tests/test_cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `list_sources`, `build_index`, `search`.
- Produces: commands `leishgene build [-o DIR] [--strict]` (default DIR `~/.cache/leishgene`), `leishgene search QUERY [-i DIR] [--limit N]`, `leishgene export [-i DIR] [-o web/data]` (copies the index and validates schema), `leishgene info` (counts, missing genomes). `export.export_site(index_dir: Path, site_data_dir: Path) -> None`. Search loads shards, injects `species` and `genome` keys from the manifest, prints a rich table (genome, seqid:start-end, strand, id, product).

- [ ] **Step 1: Write failing tests** with `click.testing.CliRunner` over a pre-built fixture index: `test_search_prints_hits`, `test_search_invalid_regex_exit_code_2_message`, `test_search_empty_query_message`, `test_info_lists_missing`, `test_export_copies_and_validates`.
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3:** Implement with rich-click, mirroring leishref's `cli.py` style.
- [ ] **Step 4:** Run; expect PASS.
- [ ] **Step 5:** Commit `feat: command line interface`.

### Task 6: Shard size budget check

**Files:**
- Create: `leishgene/budget.py`, `tests/test_budget.py`
- Modify: `leishgene/cli.py` (`export` calls it)

**Interfaces:**
- Produces: `check_budget(site_data_dir: Path, max_shard_bytes: int = 5_000_000, max_names_bytes: int = 5_000_000) -> list[str]` returning one message per violation; `export` exits non-zero if any.

- [ ] **Step 1:** Write failing tests: `test_no_violation_small`, `test_oversize_shard_reported` (write a padded file in `tmp_path`).
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3:** Implement and wire into `export`.
- [ ] **Step 4:** Run full suite; expect PASS.
- [ ] **Step 5:** Commit `feat: shard size budget check`.

### Task 7: Static site (JS matcher and UI)

**Files:**
- Create: `web/index.html`, `web/search.js`, `web/style.css`, `web/query.js` (pure matcher, no DOM), `web/tests/query.test.mjs`
- Test: `web/tests/query.test.mjs` (run with `node --test web/tests`)

**Interfaces:**
- Consumes: `tests/query_cases.json` (Task 4 vectors) and the `web/data/*.json` layout (Task 3).
- Produces: `query.js` exporting `parseQuery(text)` (throws `QueryError` with the same message class as Python) and `matches(query, gene)`; `search.js` loads `manifest.json` + `names.json` first, answers name/product/id queries from `names.json`, and lazy-loads `<genome>.json` shards (with a progress indicator) only when the query uses `ec`, `go`, `dbxref`, `type`, attrs, or the user opens a genome. Invalid queries show the error inline. Missing genomes are listed as unsearchable. Results show genome, coordinates, strand, product.

- [ ] **Step 1: Write failing test** `query.test.mjs` that loads `tests/query_cases.json` and asserts every vector (including the invalid-regex error vector).
- [ ] **Step 2:** Run `node --test web/tests`; expect FAIL.
- [ ] **Step 3:** Implement `query.js` mirroring the Task 4 tokenizer exactly; then `index.html`/`search.js`/`style.css` modelled on `/home/cokelaer/Work/github/leishref/leishref-web` (reuse its look; do not copy its catalog-specific logic).
- [ ] **Step 4:** Run node tests; expect PASS. Serve `web/` with `python -m http.server` after `leishgene export` and check a name search, an `ec:` search and an invalid regex by hand.
- [ ] **Step 5:** Commit `feat: static search site`.

### Task 8: CI, Pages deployment and docs

**Files:**
- Create: `.github/workflows/test.yml`, `.github/workflows/site.yml`, `docs/conf.py`, `docs/index.rst`, `docs/usage.rst`, `docs/Makefile`, `README.md`
- Modify: none

**Interfaces:**
- Consumes: the CLI commands (Task 5) and the budget check (Task 6).

- [ ] **Step 1:** `test.yml`: poetry install, flake8, black/isort check, pytest with coverage, `node --test web/tests`. Model on `/home/cokelaer/Work/github/leishref/.github/workflows/test.yml`.
- [ ] **Step 2:** `site.yml`: install leishref, `leishref install` for each genome with a GFF (loop over `leishgene info --list-gff-genomes`; add that flag to `info` in this task with a test in `tests/test_cli.py`), `leishgene build --strict`, `leishgene export`, publish `web/` to Pages. Model on leishref's `site.yml`.
- [ ] **Step 3:** Sphinx docs (use the `/sphinx` skill): install, CLI usage, query grammar, data layout. README with the same summary.
- [ ] **Step 4:** Run `cd docs && make html`; expect a clean build. Run `pre-commit run --all-files`; expect pass.
- [ ] **Step 5:** Commit `docs: CI, Pages deployment and documentation`.

---

## Self-review notes

- Spec coverage: scope (Task 1), data model (Task 2), data layout (Task 3), search (Tasks 4, 7), errors/missing (Tasks 3, 5), testing and size budget (Tasks 2–6), deployment (Task 8). Orthology and GFF fetching intentionally absent.
- Open item for execution: confirm that `leishref install` downloads the GFF into `~/.config/leishref/<key>/` (Task 8, step 2). If it does not, `site.yml` needs a separate download step and the plan changes there only.
