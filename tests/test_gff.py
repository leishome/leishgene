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


def test_augustus_dialect_quoted_attributes():
    genes = by_id(parse_gff(FIX / "ld1s.gff", "G"))
    g = genes["Ld1S_010012800"]
    assert (g.seqid, g.start, g.end, g.strand, g.type) == ("1", 246264, 247475, "+", "gene")
    assert g.name == "Ld1S_010012800" and g.product == "Eukaryotic initiation factor 4A-1"
    assert g.go == ["GO:0006412", "GO:0005524", "GO:0004004", "GO:0008186", "GO:0003729", "GO:0003676"] + [
        "GO:0005829",
        "GO:0016281",
    ]
    assert g.attrs == {}  # empty info, duplicated transcript_id and the folded fields are not kept


def test_augustus_dialect_na_go_is_dropped_and_semicolons_in_quotes_survive():
    genes = by_id(parse_gff(FIX / "ld1s.gff", "G"))
    assert genes["Ld1S_010013400"].go == []
    pseudo = genes["Ld1S_010010200_pseudogene"]
    assert pseudo.type == "pseudogene" and pseudo.product == "fatty acyl CoA synthetase 2, putative"
    assert pseudo.attrs["info"].startswith("has_internal_stop=true;has_frameshift=true;")
    assert pseudo.attrs["info"].endswith("original_prot_length=195")


def test_augustus_dialect_type_attribute_and_extra_attrs():
    genes = by_id(parse_gff(FIX / "ld1s.gff", "G"))
    assert genes["LD11Cs1H1_c1"].type == "snoRNA" and genes["LD11Cs1H1_c1"].go == ["GO:0009302", "GO:0006396"]
    assert genes["LD11Cs1H1_c1"].attrs == {"matchingNcRNAs": "LD11Cs1H1"}
    assert genes["LdBPK_270030140_aln1"].type == "rRNA"
    assert genes["LdBPK_270030140_aln1"].attrs["ann"] == "orthologous_to=LmjF27.rRNA.13"
    assert genes["Ld1S_100029100"].attrs == {}  # empty function=""


def test_seqid_map_renames_sequences():
    genes = parse_gff(FIX / "ld1s.gff", "G", seqid_map={"1": "CP022616.1", "27": "CP022642.1"})
    assert {g.seqid for g in genes} == {"CP022616.1", "CP022642.1", "10", "11"}


def test_embl_variant_gene_rows_collapse_into_one_gene():
    genes = by_id(parse_gff(FIX / "embl.gff", "G"))
    assert {"LMJFC_010005100", "LDHU3_01.0010"} <= set(genes)
    g = genes["LMJFC_010005100"]
    assert (g.start, g.end, g.strand, g.type) == (1504, 5117, "-", "gene")
    assert g.name == "LMJFC_010005100"
    assert g.product.startswith("Protein_of_unknown_function")
    assert g.dbxref == ["NCBI_GP:CAG9567064.1"]
    assert g.attrs["gene_biotype"] == "protein_coding"  # the coding variant wins over "other"


def test_assembly_gaps_are_not_genes():
    assert all(g.type != "gap" for g in parse_gff(FIX / "embl.gff", "G"))


def test_same_named_genes_apart_are_not_merged(tmp_path):
    path = _write(
        tmp_path,
        "c1\tx\tgene\t1\t100\t.\t+\t.\tID=gene-A1;Name=dup\n"
        "c1\tx\tgene\t500\t600\t.\t+\t.\tID=gene-A2;Name=dup\n"
        "c1\tx\tgene\t50\t150\t.\t-\t.\tID=gene-A3;Name=dup\n",
    )
    assert sorted(g.id for g in parse_gff(path, "G")) == ["A1", "A2", "A3"]


def test_variants_with_no_row_equal_to_the_name_keep_the_first_id(tmp_path):
    path = _write(
        tmp_path,
        "c1\tx\tgene\t1\t100\t.\t+\t.\tID=gene-V:CDS1;Name=V\n"
        "c1\tx\tgene\t101\t150\t.\t+\t.\tID=gene-V:5'UTR;Name=V\n",
    )
    (g,) = parse_gff(path, "G")
    assert (g.id, g.start, g.end) == ("V:CDS1", 1, 150)


def test_embl_locus_and_transcript_names_differing_by_a_trailing_t_merge():
    genes = by_id(parse_gff(FIX / "embl.gff", "G"))
    assert "LDHU3_01.0030" in genes and not any(i.endswith("T") or ":" in i for i in genes)
    g = genes["LDHU3_01.0030"]
    assert (g.start, g.end) == (2169, 5318) and g.dbxref == ["NCBI_GP:CAJ1985586.1"]


def test_pseudogene_variant_makes_the_merged_gene_a_pseudogene(tmp_path):
    path = _write(
        tmp_path,
        "c1\tx\tgene\t1\t1000\t.\t-\t.\tID=gene-P1;Name=P1;gene_biotype=other\n"
        "c1\tx\tpseudogene\t300\t800\t.\t-\t.\tID=gene-P1:CDS1;Name=P1;gene_biotype=pseudogene\n",
    )
    (g,) = parse_gff(path, "G")
    assert (g.id, g.type, g.start, g.end) == ("P1", "pseudogene", 1, 1000)
