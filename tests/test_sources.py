from pathlib import Path

import pytest
from leishref.metadata import Genome

from leishgene.sources import list_sources, load_overrides


def _genome(identifier, accession=None, gff=None, species="Leishmania donovani", strain="X"):
    files = {"fasta": f"{identifier}.fna"}
    if gff:
        files["gff"] = gff
    return Genome(identifier=identifier, accession=accession, species=species, strain=strain, files=files)


def test_list_sources_only_with_gff(tmp_path):
    genomes = [_genome("A", "GCA_1", gff="A.gff"), _genome("B", "GCA_2")]
    out = list_sources(catalog=genomes, cache_dir=tmp_path, aliases={})
    assert [s.genome_id for s in out] == ["A"]


def test_gff_path_resolved_when_cached(tmp_path):
    (tmp_path / "GCA_1").mkdir()
    (tmp_path / "GCA_1" / "A.gff").write_text("##gff-version 3\n")
    out = list_sources(catalog=[_genome("A", "GCA_1", gff="A.gff")], cache_dir=tmp_path, aliases={})
    assert out[0].gff_path == tmp_path / "GCA_1" / "A.gff"
    assert out[0].gff_name == "A.gff"


def test_gff_path_none_when_not_cached(tmp_path):
    out = list_sources(catalog=[_genome("A", "GCA_1", gff="A.gff")], cache_dir=tmp_path, aliases={})
    assert out[0].gff_path is None


def test_cache_key_falls_back_to_identifier(tmp_path):
    (tmp_path / "A").mkdir()
    (tmp_path / "A" / "A.gff").write_text("x")
    out = list_sources(catalog=[_genome("A", None, gff="A.gff")], cache_dir=tmp_path, aliases={})
    assert out[0].gff_path == Path(tmp_path / "A" / "A.gff")


def test_aliases_inverted_by_accession_or_identifier(tmp_path):
    aliases = {"Ld1": "GCA_1", "LdA": "A"}
    out = list_sources(catalog=[_genome("A", "GCA_1", gff="A.gff")], cache_dir=tmp_path, aliases=aliases)
    assert out[0].aliases == ["Ld1", "LdA"]
    assert out[0].species == "Leishmania donovani" and out[0].strain == "X"


def _overrides_file(tmp_path, genome="B"):
    (tmp_path / "extra").mkdir()
    (tmp_path / "extra" / "b.gff").write_text("##gff-version 3\n")
    path = tmp_path / "extra" / "gff_overrides.yaml"
    path.write_text(f"{genome}:\n  gff: b.gff\n  seqid_map:\n    '1': CP1.1\n")
    return path


def test_override_adds_catalog_genome_without_gff(tmp_path):
    overrides = load_overrides(_overrides_file(tmp_path))
    out = list_sources(
        catalog=[_genome("A", "GCA_1", gff="A.gff"), _genome("B", "GCA_2")],
        cache_dir=tmp_path / "c",
        aliases={},
        overrides=overrides,
    )
    assert [s.genome_id for s in out] == ["A", "B"]
    b = out[1]
    assert b.gff_path == tmp_path / "extra" / "b.gff" and b.gff_name == "b.gff" and b.override
    assert b.seqid_map == {"1": "CP1.1"} and b.species == "Leishmania donovani"
    assert not out[0].override and out[0].seqid_map == {}


def test_override_wins_over_catalog_gff(tmp_path):
    overrides = load_overrides(_overrides_file(tmp_path, "A"))
    out = list_sources(
        catalog=[_genome("A", "GCA_1", gff="A.gff")], cache_dir=tmp_path / "c", aliases={}, overrides=overrides
    )
    assert len(out) == 1 and out[0].gff_path == tmp_path / "extra" / "b.gff"


def test_override_for_unknown_genome_is_an_error(tmp_path):
    overrides = load_overrides(_overrides_file(tmp_path, "Z"))
    with pytest.raises(ValueError, match="Z"):
        list_sources(catalog=[_genome("A", "GCA_1")], cache_dir=tmp_path, aliases={}, overrides=overrides)


def test_override_with_missing_file_is_an_error(tmp_path):
    path = _overrides_file(tmp_path)
    (tmp_path / "extra" / "b.gff").unlink()
    with pytest.raises(FileNotFoundError, match="b.gff"):
        load_overrides(path)
