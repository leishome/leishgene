Usage
=====

Install, then make sure the genomes you want are in the leishref cache
(``leishref install NAME --alias ALIAS``). Only catalog genomes that record a GFF are indexed, plus the ones listed in
``data/extra/gff_overrides.yaml`` (see :doc:`data`).

.. code-block:: console

   $ pip install leishgene
   $ leishgene build                      # parse cached GFFs into ~/.cache/leishgene
   $ leishgene search 'kinase species:donovani'
   $ leishgene search kinase -o kinases.tsv   # also write every match to a .tsv or .csv file
   $ leishgene info                       # genomes in the index, and those missing a GFF
   $ leishgene export -o web/data         # data for the static website

``leishgene build --overrides FILE`` reads another overrides file (default ``data/extra/gff_overrides.yaml``,
used when it exists). ``leishgene build --strict`` fails when a catalog GFF is not cached instead of skipping it.
``leishgene export`` fails when a file exceeds the size budget (5 MB gzipped).

To try the website locally: ``leishgene export -o web/data && python -m http.server --directory web``.

On the website, the TSV and CSV buttons above the results (with an optional file name box) download every match of the current search, not only
the rows shown. Columns: genome, species, seqid, start, end, strand, id, name, type, product, ec, go, dbxref
(list values joined with ``;``). ``leishgene search QUERY -o FILE`` writes the same table.
