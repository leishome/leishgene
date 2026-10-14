import json
from pathlib import Path

from leishgene.export import export_site
from leishgene.gff import read_seqlens
from leishgene.index import build_index
from leishgene.sources import GenomeSource


def _gff(tmp_path, text):
    path = tmp_path / "t.gff"
    path.write_text("##gff-version 3\n" + text)
    return path


def test_read_seqlens_from_sequence_region_and_region_rows(tmp_path):
    path = _gff(
        tmp_path,
        "##sequence-region chr1 1 5000\n"
        "chr2\tx\tregion\t1\t7000\t.\t+\t.\tID=chr2:1..7000\n"
        "chr1\tx\tgene\t10\t20\t.\t+\t.\tID=g1\n",
    )
    assert read_seqlens(path) == {"chr1": 5000, "chr2": 7000}


def test_read_seqlens_applies_seqid_map_and_is_empty_without_declarations(tmp_path):
    path = _gff(tmp_path, "##sequence-region 1 1 99\n")
    assert read_seqlens(path, {"1": "CP1.1"}) == {"CP1.1": 99}
    assert read_seqlens(_gff(tmp_path, "c\tx\tgene\t1\t2\t.\t+\t.\tID=g\n")) == {}


def _source(path, name="G1"):
    return GenomeSource(name, path.name, "Leishmania x", "S", [], path)


def test_index_writes_seqlens_for_sequences_with_genes(tmp_path):
    path = _gff(
        tmp_path,
        "##sequence-region c1 1 500\n##sequence-region c2 1 900\n##sequence-region c3 1 50\n"
        "c1\tx\tgene\t10\t20\t.\t+\t.\tID=g1\n"
        "c2\tx\tgene\t10\t1000\t.\t+\t.\tID=g2\n"  # longer than declared: the gene end wins
        "c4\tx\tgene\t5\t60\t.\t+\t.\tID=g3\n",  # nothing declared: the gene end stands in
    )
    build_index(tmp_path / "idx", [_source(path)])
    assert json.loads((tmp_path / "idx" / "seqlens.json").read_text()) == {"G1": {"c1": 500, "c2": 1000, "c4": 60}}


def test_export_copies_seqlens(tmp_path):
    path = _gff(tmp_path, "c1\tx\tgene\t10\t20\t.\t+\t.\tID=g1\n")
    build_index(tmp_path / "idx", [_source(path)])
    export_site(tmp_path / "idx", tmp_path / "site")
    assert (tmp_path / "site" / "seqlens.json").is_file()
