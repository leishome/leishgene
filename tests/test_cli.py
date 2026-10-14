import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from leishgene.cli import cli
from leishgene.index import build_index
from leishgene.sources import GenomeSource

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def index_dir(tmp_path):
    sources = [
        GenomeSource("G1", "ncbi.gff", "Leishmania donovani", "S1", [], FIX / "ncbi.gff"),
        GenomeSource("G2", "tritryp.gff", "Leishmania major", "S2", [], FIX / "tritryp.gff"),
        GenomeSource("G3", "gone.gff", "Leishmania tropica", "S3", [], None),
    ]
    out = tmp_path / "index"
    build_index(out, sources)
    return out


def run(*args):
    return CliRunner().invoke(cli, [str(a) for a in args], env={"COLUMNS": "250"})


def test_search_prints_hits(index_dir):
    result = run("search", "kinase", "-i", index_dir)
    assert result.exit_code == 0, result.output
    assert "LMJF_01_0020" in result.output and "protein kinase" in result.output
    assert "LdBPK_010010" not in result.output


def test_search_species_filter_uses_manifest(index_dir):
    result = run("search", "species:major", "-i", index_dir)
    assert "LdBPK_010010" in result.output and "LMJF_01_0020" not in result.output


def test_search_invalid_regex_exit_code_2_message(index_dir):
    result = run("search", "/(/", "-i", index_dir)
    assert result.exit_code == 2
    assert "invalid regular expression" in result.output
    assert "Traceback" not in result.output


def test_search_empty_query_message(index_dir):
    result = run("search", "  ", "-i", index_dir)
    assert result.exit_code == 0
    assert "empty query" in result.output.lower()


def test_search_without_index_is_clear_error(tmp_path):
    result = run("search", "x", "-i", tmp_path / "nope")
    assert result.exit_code != 0 and "leishgene build" in result.output


def test_info_lists_missing(index_dir):
    result = run("info", "-i", index_dir)
    assert result.exit_code == 0
    assert "G3" in result.output and "missing" in result.output
    assert "G1" in result.output


def test_export_copies_and_validates(index_dir, tmp_path):
    out = tmp_path / "site"
    result = run("export", "-i", index_dir, "-o", out)
    assert result.exit_code == 0, result.output
    assert json.loads((out / "manifest.json").read_text())[0]["genome"] == "G1"
    assert (out / "G1.json").exists() and (out / "names.json").exists()
    assert not (out / "G3.json").exists()


def test_export_rejects_incomplete_index(index_dir, tmp_path):
    (index_dir / "G1.json").unlink()
    result = run("export", "-i", index_dir, "-o", tmp_path / "site")
    assert result.exit_code != 0 and "G1" in result.output


def test_export_fails_over_budget(index_dir, tmp_path, monkeypatch):
    import leishgene.cli as cli_module

    monkeypatch.setattr(cli_module, "check_budget", lambda path: ["G1.json: 9 MB gzipped exceeds 5 MB"])
    result = run("export", "-i", index_dir, "-o", tmp_path / "site")
    assert result.exit_code != 0 and "exceeds" in result.output


def test_info_list_gff_genomes_prints_catalog_ids(monkeypatch):
    import leishgene.cli as cli_module

    monkeypatch.setattr(
        cli_module,
        "list_sources",
        lambda: [GenomeSource("A", "a.gff", None, None, [], None), GenomeSource("B", "b.gff", None, None, [], None)],
    )
    result = run("info", "--list-gff-genomes")
    assert result.exit_code == 0
    assert result.output.split() == ["A", "B"]


def test_search_prints_bracketed_product_literally(tmp_path):
    out = tmp_path / "idx"
    out.mkdir()
    gene = {"genome": "G", "seqid": "c", "start": 1, "end": 2, "strand": "+", "type": "gene", "id": "g1", "name": "g1"}
    genes = [
        dict(gene, product="enoyl-[acyl-carrier-protein] reductase"),
        dict(gene, id="g2", product="bad [/x] markup"),
    ]
    (out / "G.json").write_text(json.dumps(genes))
    (out / "names.json").write_text("[]")
    (out / "manifest.json").write_text(
        json.dumps([{"genome": "G", "species": "s", "strain": "", "aliases": [], "genes": 2, "status": "ok"}])
    )
    result = CliRunner().invoke(cli, ["search", "g*", "-i", str(out)], env={"COLUMNS": "250"})
    assert result.exit_code == 0, result.output
    assert "enoyl-[acyl-carrier-protein] reductase" in result.output
    assert "bad [/x] markup" in result.output


def test_export_ships_shard_of_empty_genome(tmp_path):
    empty = tmp_path / "e.gff"
    empty.write_text("##gff-version 3\n")
    idx = tmp_path / "idx"
    build_index(idx, [GenomeSource("E", "e.gff", "s", None, [], empty)])
    result = run("export", "-i", idx, "-o", tmp_path / "site")
    assert result.exit_code == 0, result.output
    assert (tmp_path / "site" / "E.json").exists()


def test_build_with_overrides_file(tmp_path, monkeypatch):
    import leishgene.cli as cli_module

    (tmp_path / "x.gff").write_text((FIX / "ld1s.gff").read_text())
    overrides = tmp_path / "gff_overrides.yaml"
    overrides.write_text("G9:\n  gff: x.gff\n  seqid_map:\n    '1': CP1.1\n")
    seen = {}

    def fake_list_sources(overrides=None):
        seen["overrides"] = overrides
        return [
            GenomeSource(
                "G9",
                "x.gff",
                "Leishmania donovani",
                "1S",
                [],
                overrides["G9"].gff_path,
                overrides["G9"].seqid_map,
                True,
            )
        ]

    monkeypatch.setattr(cli_module, "list_sources", fake_list_sources)
    out = tmp_path / "idx"
    result = run("build", "-i", out, "--overrides", overrides)
    assert result.exit_code == 0, result.output
    assert seen["overrides"]["G9"].seqid_map == {"1": "CP1.1"}
    assert {g["seqid"] for g in json.loads((out / "G9.json").read_text())} >= {"CP1.1"}


def test_build_without_overrides_file_uses_catalog_only(tmp_path, monkeypatch):
    import leishgene.cli as cli_module

    monkeypatch.chdir(tmp_path)  # no data/extra/gff_overrides.yaml here
    seen = {}
    monkeypatch.setattr(cli_module, "list_sources", lambda overrides=None: seen.setdefault("o", overrides) or [])
    result = run("build", "-i", tmp_path / "idx")
    assert result.exit_code == 0, result.output
    assert seen["o"] in (None, {})


def test_search_output_writes_all_matches_not_just_limit(index_dir, tmp_path):
    out = tmp_path / "hits.tsv"
    result = run("search", "*", "-i", index_dir, "--limit", 1, "--output", out)
    assert result.exit_code == 0, result.output
    lines = out.read_text().splitlines()
    assert lines[0].split("\t")[:4] == ["genome", "species", "strain", "seqid"]
    assert len(lines) - 1 > 1  # more rows than --limit
    assert "wrote" in result.output and str(out) in result.output.replace("\n", "")


def test_search_output_rejects_unknown_extension(index_dir, tmp_path):
    result = run("search", "kinase", "-i", index_dir, "--output", tmp_path / "hits.txt")
    assert result.exit_code != 0 and ".tsv" in result.output
