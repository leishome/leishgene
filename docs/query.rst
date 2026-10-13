Query grammar
=============

Terms are separated by whitespace and AND-ed. Matching is case-insensitive.

========================  ==============================================
``kinase``                substring
``kinas*``                glob (``*`` matches anything)
``/^LdBPK_\d+$/``         regular expression
``"protein kinase"``      phrase
``field:term``            restrict the term to one field
========================  ==============================================

Fields: ``id name product type species genome ec go dbxref``. A ``word:`` prefix that is not a field
(``GO:0004672``, ``GeneID:123``) is part of the term. Bare terms search id, name, product, EC, GO, Dbxref
the remaining GFF attributes, and the genome (catalog id, strain, aliases) and species names, so
``Ld1S kinase`` finds kinases of Ld1S. ``genome:`` matches the catalog id, the strain and the aliases
(``genome:Ld1S``, ``genome:pasteur``). An empty query matches nothing; an invalid regular expression is an error.

The Python (``leishgene/search.py``) and JavaScript (``web/query.js``) matchers are checked against the same
vectors in ``tests/query_cases.json``.

.. note::
   The NCBI GFFs of the current catalog carry no EC or GO terms, so ``ec:`` and ``go:`` only match genomes
   annotated by sources that provide them (for example TriTrypDB).
