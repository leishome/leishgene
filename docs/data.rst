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
