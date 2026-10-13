"""Which leishref catalog genomes have a GFF, and where it lives in the local cache."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from leishref import metadata


@dataclass
class GenomeSource:
    genome_id: str
    gff_name: str
    species: Optional[str] = None
    strain: Optional[str] = None
    aliases: list = field(default_factory=list)
    gff_path: Optional[Path] = None
    seqid_map: dict = field(default_factory=dict)  # GFF sequence name -> name in the catalog FASTA
    override: bool = False  # GFF comes from the overrides file, not from the leishref catalog


@dataclass
class GffOverride:
    gff_path: Path
    seqid_map: dict = field(default_factory=dict)


def load_overrides(path) -> dict:
    """Read a YAML file of GFFs that replace or complete the leishref catalog.

    ``{genome_id: {gff: <file, relative to the YAML>, seqid_map: {<gff name>: <catalog name>}}}``.
    Raises FileNotFoundError when a listed GFF does not exist.
    """
    path = Path(path)
    overrides = {}
    for genome_id, spec in (yaml.safe_load(path.read_text()) or {}).items():
        gff = path.parent / spec["gff"]
        if not gff.is_file():
            raise FileNotFoundError(f"{genome_id}: {gff} (listed in {path}) does not exist")
        overrides[str(genome_id)] = GffOverride(gff, {str(k): str(v) for k, v in (spec.get("seqid_map") or {}).items()})
    return overrides


def list_sources(catalog=None, cache_dir=None, aliases=None, overrides=None) -> list:
    """Genomes of the leishref catalog that record a GFF, or that have an entry in ``overrides``.

    An override (see ``load_overrides``) wins over the catalog GFF. Overrides naming a genome that is
    not in the catalog raise ValueError.

    ``gff_path`` is the cached file (``<cache>/<accession or identifier>/<gff name>``), or None
    when it has not been installed locally.
    """
    genomes = metadata.catalog() if catalog is None else catalog
    cache = Path(metadata.CACHE_DIR if cache_dir is None else cache_dir)
    alias_map = metadata.load_aliases() if aliases is None else aliases
    by_target: dict = {}
    for alias, target in alias_map.items():
        by_target.setdefault(target, []).append(alias)

    overrides = overrides or {}
    unknown = set(overrides) - {g.identifier for g in genomes}
    if unknown:
        raise ValueError(f"GFF overrides for genomes not in the catalog: {', '.join(sorted(unknown))}")

    sources = []
    for genome in genomes:
        names = by_target.get(genome.identifier, []) + by_target.get(genome.accession or "", [])
        override = overrides.get(genome.identifier)
        if override:
            sources.append(
                GenomeSource(
                    genome_id=genome.identifier,
                    gff_name=override.gff_path.name,
                    species=genome.species,
                    strain=genome.strain,
                    aliases=sorted(set(names)),
                    gff_path=override.gff_path,
                    seqid_map=override.seqid_map,
                    override=True,
                )
            )
            continue
        if not genome.gff:
            continue
        key = genome.accession or genome.identifier
        path = cache / key / genome.gff
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
