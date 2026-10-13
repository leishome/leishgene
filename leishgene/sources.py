"""Which leishref catalog genomes have a GFF, and where it lives in the local cache."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from leishref import metadata


@dataclass
class GenomeSource:
    genome_id: str
    gff_name: str
    species: Optional[str] = None
    strain: Optional[str] = None
    aliases: list = field(default_factory=list)
    gff_path: Optional[Path] = None


def list_sources(catalog=None, cache_dir=None, aliases=None) -> list:
    """Genomes of the leishref catalog that record a GFF.

    ``gff_path`` is the cached file (``<cache>/<accession or identifier>/<gff name>``), or None
    when it has not been installed locally.
    """
    genomes = metadata.catalog() if catalog is None else catalog
    cache = Path(metadata.CACHE_DIR if cache_dir is None else cache_dir)
    alias_map = metadata.load_aliases() if aliases is None else aliases
    by_target: dict = {}
    for alias, target in alias_map.items():
        by_target.setdefault(target, []).append(alias)

    sources = []
    for genome in genomes:
        if not genome.gff:
            continue
        key = genome.accession or genome.identifier
        path = cache / key / genome.gff
        names = by_target.get(genome.identifier, []) + by_target.get(genome.accession or "", [])
        sources.append(
            GenomeSource(
                genome_id=genome.identifier,
                gff_name=genome.gff,
                species=genome.species,
                strain=genome.strain,
                aliases=sorted(set(names)),
                gff_path=path if path.is_file() else None,
            )
        )
    return sources
