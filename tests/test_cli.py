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
    return CliRunner().invoke(cli, [str(a) for a in args])


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
