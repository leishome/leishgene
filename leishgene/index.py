"""Build the search index: one JSON shard per genome, a manifest and a names index."""
import json
import logging
from collections import Counter
from pathlib import Path

from leishgene.gff import parse_gff, read_seqlens

log = logging.getLogger(__name__)


class MissingGffError(RuntimeError):
    """A catalog genome records a GFF that is not in the local cache."""


def _dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, separators=(",", ":")))


def _sequence_lengths(source, genes) -> dict:
    """Length of every sequence that carries a gene: as the GFF declares it, at least as far as its last gene."""
    longest: dict = {}
    for gene in genes:
        longest[gene.seqid] = max(longest.get(gene.seqid, 0), gene.end)
    declared = read_seqlens(source.gff_path, source.seqid_map)
    return {seqid: max(end, declared.get(seqid, 0)) for seqid, end in longest.items()}


def build_index(out_dir: Path, sources: list, strict: bool = False) -> list:
    """Write ``<genome>.json`` shards, ``manifest.json``, ``names.json`` and ``seqlens.json`` into ``out_dir``.

    Returns the manifest. A genome whose GFF is not cached is recorded with status "missing"
    (or raises MissingGffError when ``strict``); one with no genes has status "empty".
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest, names, seqlens = [], [], {}
    for index, source in enumerate(sources):
        entry = {
            "genome": source.genome_id,
            "species": source.species,
            "strain": source.strain,
            "aliases": list(source.aliases),
            "gff": source.gff_name,
            "source": "local override" if source.override else "leishref catalog",
            "genes": 0,
            "types": {},
            "status": "ok",
        }
        if source.gff_path is None:
            if strict:
                raise MissingGffError(f"{source.genome_id}: {source.gff_name} is not in the local cache")
            log.warning("%s: %s is not in the local cache, skipped", source.genome_id, source.gff_name)
            entry["status"] = "missing"
            manifest.append(entry)
            continue
        genes = parse_gff(source.gff_path, source.genome_id, source.seqid_map)
        entry["genes"] = len(genes)
        entry["types"] = dict(Counter(g.type for g in genes).most_common())
        if not genes:
            entry["status"] = "empty"
        _dump(out_dir / f"{source.genome_id}.json", [g.to_dict() for g in genes])
        seqlens[source.genome_id] = _sequence_lengths(source, genes)
        names.extend([index, g.id, g.name, g.product] for g in genes)
        manifest.append(entry)
    _dump(out_dir / "manifest.json", manifest)
    _dump(out_dir / "names.json", names)
    _dump(out_dir / "seqlens.json", seqlens)
    return manifest
