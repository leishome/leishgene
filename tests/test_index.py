import json
import logging
from collections import Counter
from pathlib import Path

import pytest

from leishgene.index import MissingGffError, build_index
from leishgene.sources import GenomeSource

FIX = Path(__file__).parent / "fixtures"


def src(genome_id, name, path):
    return GenomeSource(
        genome_id=genome_id, gff_name=name, species="Leishmania x", strain="S", aliases=["al"], gff_path=path
    )


def load(path):
    return json.loads(Path(path).read_text())


def test_writes_shard_manifest_names(tmp_path):
    manifest = build_index(tmp_path, [src("G1", "ncbi.gff", FIX / "ncbi.gff")])
    assert manifest == load(tmp_path / "manifest.json")
    assert manifest == [
        {
            "genome": "G1",
            "species": "Leishmania x",
            "strain": "S",
            "aliases": ["al"],
            "gff": "ncbi.gff",
            "source": "leishref catalog",
            "genes": 3,
            "types": manifest[0]["types"],
            "status": "ok",
        }
    ]
    shard = load(tmp_path / "G1.json")
    assert {g["id"] for g in shard} == {"LMJF_01_0010", "LMJF_01_0020", "LMJF_tRNA1"}
    assert shard[0]["genome"] == "G1"


def test_names_rows_reference_manifest_index(tmp_path):
    build_index(tmp_path, [src("G1", "ncbi.gff", FIX / "ncbi.gff"), src("G2", "tritryp.gff", FIX / "tritryp.gff")])
    names = load(tmp_path / "names.json")
    assert [0, "LMJF_01_0020", "LMJF_01_0020", "protein kinase"] in names
    assert [1, "LdBPK_010010", "LdBPK_010010", "kinesin, putative"] in names
    assert len(names) == 4


def test_missing_gff_recorded_not_fatal(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        manifest = build_index(tmp_path, [src("G1", "ncbi.gff", None)])
    assert manifest[0]["status"] == "missing" and manifest[0]["genes"] == 0
    assert not (tmp_path / "G1.json").exists()
    assert "G1" in caplog.text


def test_strict_raises_on_missing(tmp_path):
    with pytest.raises(MissingGffError):
        build_index(tmp_path, [src("G1", "ncbi.gff", None)], strict=True)


def test_zero_gene_genome_status_ok_count_zero(tmp_path):
    empty = tmp_path / "empty.gff"
    empty.write_text("##gff-version 3\n")
    manifest = build_index(tmp_path / "out", [src("G1", "empty.gff", empty)])
    assert manifest[0]["status"] == "empty" and manifest[0]["genes"] == 0
    assert load(tmp_path / "out" / "G1.json") == []


def test_seqid_map_applied_to_shard(tmp_path):
    source = src("G1", "ld1s.gff", FIX / "ld1s.gff")
    source.seqid_map = {"1": "CP022616.1"}
    build_index(tmp_path, [source])
    seqids = {g["seqid"] for g in load(tmp_path / "G1.json")}
    assert "CP022616.1" in seqids and "1" not in seqids


def test_manifest_counts_genes_by_type(tmp_path):
    manifest = build_index(tmp_path, [src("G1", "ncbi.gff", FIX / "ncbi.gff")])
    assert manifest[0]["types"] == dict(Counter(g["type"] for g in load(tmp_path / "G1.json")))
    assert sum(manifest[0]["types"].values()) == manifest[0]["genes"] == 3


def test_manifest_records_gff_and_source(tmp_path):
    local = src("G2", "ld1s.gff", FIX / "ld1s.gff")
    local.override = True
    manifest = build_index(tmp_path, [src("G1", "ncbi.gff", FIX / "ncbi.gff"), local])
    assert [(e["gff"], e["source"]) for e in manifest] == [
        ("ncbi.gff", "leishref catalog"),
        ("ld1s.gff", "local override"),
    ]
