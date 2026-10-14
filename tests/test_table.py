import csv

import pytest

from leishgene.table import COLUMNS, write_table

GENE = {
    "genome": "G1",
    "species": "Leishmania donovani",
    "strain": "pasteur",
    "strain": "pasteur",
    "seqid": "c1",
    "start": 5,
    "end": 90,
    "strand": "-",
    "id": "g1",
    "name": "g1",
    "type": "gene",
    "product": 'kinase, "putative"\tline',
    "ec": ["2.7.11.1", "2.7.1.1"],
    "go": [],
    "dbxref": ["GeneID:1"],
}


def test_columns_are_fixed():
    assert (
        list(COLUMNS)
        == "genome species strain seqid start end length strand id name type product ec go dbxref uniprot".split()
    )


def test_write_tsv_quotes_and_joins_lists(tmp_path):
    out = tmp_path / "hits.tsv"
    write_table([GENE], out)
    header, row = out.read_text().splitlines()
    assert header == "\t".join(COLUMNS)
    assert (
        row
        == 'G1\tLeishmania donovani\tpasteur\tc1\t5\t90\t86\t-\tg1\tg1\tgene\t"kinase, ""putative""\tline"\t2.7.11.1;2.7.1.1\t\tGeneID:1\t'
    )


def test_write_csv_quotes_commas(tmp_path):
    out = tmp_path / "hits.csv"
    write_table([GENE], out)
    assert '"kinase, ""putative""\tline"' in out.read_text().splitlines()[1]


def test_unknown_extension_is_an_error(tmp_path):
    with pytest.raises(ValueError, match=".txt"):
        write_table([GENE], tmp_path / "hits.txt")


def test_length_and_uniprot_columns(tmp_path):
    out = tmp_path / "hits.tsv"
    gene = dict(
        GENE, dbxref=["UniProtKB/TrEMBL:E9ABZ0", "UniProtKB/Swiss-Prot:P1", "UniProtKB/TrEMBL:E9ABZ0", "GeneID:1"]
    )
    write_table([gene], out)
    with open(out, newline="") as handle:
        header, row = list(csv.reader(handle, delimiter="\t"))
    cols = dict(zip(header, row))
    assert cols["length"] == "86" and cols["uniprot"] == "E9ABZ0;P1" and cols["product"].startswith("kinase, ")
