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
