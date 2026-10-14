Data layout
===========

``web/data/`` (and the index directory) contains:

* ``<genome>.json``: one list of gene records per genome (genome, seqid, start, end, strand, type, id, name,
  product, ec, go, dbxref, attrs). Children (mRNA, CDS, ncRNA...) are folded into their gene; rows without a
  gene parent are kept as their own record.
* ``manifest.json``: genome, species, strain, aliases, gene count and status (``ok`` or ``missing``).
* ``names.json``: ``[genome index, id, name, product]`` for every gene, for instant first-pass search.

The page answers id/name/product queries from ``names.json`` and loads only the shards of the genomes it
shows. ``type:``, ``ec:``, ``go:``, ``dbxref:`` filters and the "search all annotation fields" option load
every shard.

GFFs outside the catalog
------------------------

``data/extra/gff_overrides.yaml`` lists GFFs that the leishref catalog lacks, or that should replace its own.
Each entry is a catalog genome with the GFF path (relative to the YAML file) and an optional ``seqid_map`` that
renames the GFF sequences to the names of the catalog FASTA, so the coordinates read the same everywhere:

.. code-block:: yaml

   GCA_002243465.1:
     gff: Ld1S.gff
     seqid_map:
       '1': CP022616.1

``Ld1S.gff`` annotates the Ld1S assembly (*L. donovani*, GCA_002243465.1 has no annotation at NCBI). Its
attributes are AUGUSTUS-style ``key="value"``: ``gene_id`` becomes the id, ``combinedAnnotation`` the product,
``BP``/``MF``/``CC`` are merged into the GO terms (``NA`` dropped) and ``type`` (pseudogene, snoRNA, ...) the
record type. Rows repeating an id, such as the gene and rRNA rows of one rRNA, are one record.

Each ``manifest.json`` entry also records the annotation file (``gff``), where it came from (``source``:
``leishref catalog`` or ``local override``) and the number of genes per type (``types``). The website's
``about.html`` ("What is included" in the header and footer) is built from it and lists every genome with its
strain, aliases, annotation file and gene count, the genomes that could not be searched, and the limits of the
data.

Variant rows of one gene
------------------------

Assembly gaps (``gap``) are not indexed. Some EMBL-derived GFFs write one ``gene`` row per feature of a locus
(the locus, its transcript ``<locus>T``, ``:E1``, ``:CDS1``, ``:3'UTR``, ``:5'UTR``). Gene-level rows of the same
sequence and strand whose names match (a trailing ``T`` is ignored) and that overlap or touch are merged into a
single record: the row whose id is the name leads, the span is the union, products and cross-references are
combined, a ``protein_coding`` biotype wins over ``other`` and a ``pseudogene`` variant makes the gene a pseudogene.
