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
(list values joined with ``;``); ``length`` is ``end - start + 1`` in bp and ``uniprot`` the UniProtKB accessions of the
Dbxref values. ``leishgene search QUERY -o FILE`` writes the same table.

Above the table, two bar charts count all matches of the search (not only the rows shown): matches per genome
(top 12, the rest folded into "others") and matches by type (shown when the search loads the genome data,
that is with "search all annotation fields" or a ``type:``, ``ec:``, ``go:`` or ``dbxref:`` term). A click on a
bar adds ``genome:ID`` or ``type:NAME`` to the query. The table and the exports include the strain.

The "links" column of the table gives the UniProt entry of each ``UniProtKB/TrEMBL`` or ``UniProtKB/Swiss-Prot``
Dbxref, and a UniParc search on the protein accession (``protein_id``, else ``NCBI_GP``). The GFFs carry no
UniParc identifier, so that link is a search that lands on the matching UniParc entry. Genomes whose GFF has no
such cross-references, such as Ld1S, get no links.

A click (or Enter) on a table row unfolds the EC numbers, GO terms, Dbxref values and remaining GFF attributes of
the gene; EC, GO, GeneID, InterPro, PFAM, PDB and UniProt references are links. The address bar always holds the
current search (``?q=...&all=1``), so a search can be shared by copying the URL. The "links" column adds an NCBI
Gene link from the ``GeneID`` Dbxref.
