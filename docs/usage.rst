Usage
=====

Install, then make sure the genomes you want are in the leishref cache
(``leishref install NAME --alias ALIAS``). Only catalog genomes that record a GFF are indexed, plus the ones listed in
``data/extra/gff_overrides.yaml`` (see :doc:`data`).

.. code-block:: console

   $ pip install leishgene
   $ leishgene build                      # parse cached GFFs into ~/.cache/leishgene
   $ leishgene search 'kinase species:donovani'
   $ leishgene info                       # genomes in the index, and those missing a GFF
   $ leishgene export -o web/data         # data for the static website

``leishgene build --overrides FILE`` reads another overrides file (default ``data/extra/gff_overrides.yaml``,
used when it exists). ``leishgene build --strict`` fails when a catalog GFF is not cached instead of skipping it.
``leishgene export`` fails when a file exceeds the size budget (5 MB gzipped).

To try the website locally: ``leishgene export -o web/data && python -m http.server --directory web``.
