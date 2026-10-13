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


def test_attrs_omit_keys_already_in_fields():
    genes = by_id(parse_gff(FIX / "ncbi.gff", "G1"))
    attrs = genes["LMJF_01_0010"].attrs
    assert not {"Name", "product", "description", "Dbxref", "Ontology_term", "ec_number", "EC_number"} & set(attrs)


def _write(tmp_path, text):
    path = tmp_path / "t.gff"
    path.write_text("##gff-version 3\n" + text)
    return path


def test_orphan_mrna_folds_its_cds(tmp_path):
    path = _write(
        tmp_path,
        "c1\tx\tmRNA\t10\t90\t.\t+\t.\tID=rna-XM_1;product=kinase\n"
        "c1\tx\tCDS\t10\t40\t.\t+\t0\tID=cds-1;Parent=rna-XM_1;Dbxref=GeneID:1\n"
        "c1\tx\tCDS\t50\t90\t.\t+\t0\tID=cds-1;Parent=rna-XM_1;Dbxref=GeneID:1\n",
    )
    (g,) = parse_gff(path, "G")
    assert g.id == "rna-XM_1" and g.type == "mRNA" and g.dbxref == ["GeneID:1"] and g.product == "kinase"


def test_discontinuous_gene_rows_with_same_id_merge(tmp_path):
    path = _write(
        tmp_path,
        "c1\tx\tpseudogene\t482801\t483807\t.\t-\t.\tID=gene-P1;Name=P1\n"
        "c1\tx\tpseudogene\t481920\t482799\t.\t-\t.\tID=gene-P1;Name=P1\n"
        "c1\tx\tCDS\t481920\t482799\t.\t-\t0\tID=cds-p1;Parent=gene-P1;product=pseudo kinase\n",
    )
    (g,) = parse_gff(path, "G")
    assert (g.id, g.start, g.end, g.product) == ("P1", 481920, 483807, "pseudo kinase")


def test_veupathdb_protein_coding_gene_and_polypeptide(tmp_path):
    path = _write(
        tmp_path,
        "c1\tVEuPathDB\tprotein_coding_gene\t1\t90\t.\t+\t.\tID=LdBPK_1;description=kinesin\n"
        "c1\tVEuPathDB\tmRNA\t1\t90\t.\t+\t.\tID=LdBPK_1.1;Parent=LdBPK_1\n"
        "c1\tVEuPathDB\tCDS\t1\t90\t.\t+\t0\tID=cds_LdBPK_1.1;Parent=LdBPK_1.1\n"
        "c1\tVEuPathDB\tpolypeptide\t1\t90\t.\t+\t.\tID=LdBPK_1.1.p;Derives_from=LdBPK_1.1\n",
    )
    (g,) = parse_gff(path, "G")
    assert g.id == "LdBPK_1" and g.type == "protein_coding_gene" and g.product == "kinesin"
