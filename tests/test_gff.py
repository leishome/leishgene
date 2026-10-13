from pathlib import Path

from leishgene.gff import parse_gff

FIX = Path(__file__).parent / "fixtures"


def by_id(genes):
    return {g.id: g for g in genes}


def test_ncbi_gene_folds_children():
    genes = by_id(parse_gff(FIX / "ncbi.gff", "G1"))
    assert set(genes) == {"LMJF_01_0010", "LMJF_01_0020", "LMJF_tRNA1"}
    g = genes["LMJF_01_0010"]
    assert (g.genome, g.seqid, g.start, g.end, g.strand, g.type) == ("G1", "chr1", 3704, 4702, "-", "gene")
    assert g.name == "LMJF_01_0010"
    assert g.product == "hypothetical protein"
    assert g.dbxref == ["InterPro:IPR021333", "UniProtKB/TrEMBL:E9ABZ0"]
    assert genes["LMJF_01_0020"].product == "protein kinase"  # via mRNA
    assert genes["LMJF_01_0020"].ec == ["2.7.11.1"]  # via CDS under mRNA
    assert genes["LMJF_tRNA1"].product == "tRNA-Ala"


def test_tritryp_description_and_go_ec():
    (g,) = parse_gff(FIX / "tritryp.gff", "G2")
    assert g.id == "LdBPK_010010"
    assert g.product == "kinesin, putative"
    assert g.go == ["GO:0003777", "GO:0005524"]
    assert g.ec == ["3.6.4.4"]
    assert g.attrs["ebi_biotype"] == "protein_coding"


def test_percent_decoded_not_split():
    genes = by_id(parse_gff(FIX / "edge.gff.gz", "G3"))
    assert genes["cds-orph"].product == "hypothetical, putative; x=y"


def test_orphan_rows_become_own_rows():
    genes = by_id(parse_gff(FIX / "edge.gff.gz", "G3"))
    assert genes["cds-orph"].type == "CDS"
    assert genes["rna-NOGENE"].type == "mRNA"
    assert genes["PSEUDO1"].type == "pseudogene"


def test_unknown_attrs_kept_verbatim():
    genes = by_id(parse_gff(FIX / "ncbi.gff", "G1"))
    assert genes["LMJF_01_0010"].attrs["gbkey"] == "Gene"
    assert genes["LMJF_01_0010"].attrs["Note"] == "previous protein_id=AAC24613.1"  # folded from CDS


def test_fasta_section_and_non_feature_rows_ignored():
    genes = parse_gff(FIX / "ncbi.gff", "G1")
    assert all(g.type != "region" for g in genes)
    assert all(g.id != "chr1" for g in genes)


def test_to_dict_keys():
    (g,) = parse_gff(FIX / "tritryp.gff", "G2")
    assert set(g.to_dict()) == {
        "genome",
        "seqid",
        "start",
        "end",
        "strand",
        "type",
        "id",
        "name",
        "product",
        "ec",
        "go",
        "dbxref",
        "attrs",
    }
