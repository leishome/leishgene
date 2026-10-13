from pathlib import Path

from leishref.metadata import Genome

from leishgene.sources import list_sources


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
