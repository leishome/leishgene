# leishgene

Search genes and annotations across the *Leishmania* genomes of the [leishref](https://github.com/leishome/leishref)
catalog that have a GFF (38 at the time of writing, plus Ld1S from `data/extra/`): a Python package and a static website.

```bash
pip install leishgene
leishgene build                              # parse the GFFs cached by `leishref install`
leishgene search 'kinase species:donovani'
leishgene search '/^LdBPK_27\d+$/'
leishgene export -o web/data                 # data for the static site in web/
```

Query grammar: words are AND-ed; `kinas*` globs; `/regex/`; `"phrases"`; `field:value` with
`id name product type species genome ec go dbxref`. See `docs/` (build with `cd docs && make html`).

Not in scope yet: fetching GFFs for genomes that lack one, orthology.
