"""Build the search index: one JSON shard per genome, a manifest and a names index."""
import json
import logging
from pathlib import Path

from leishgene.gff import parse_gff

log = logging.getLogger(__name__)


class MissingGffError(RuntimeError):
    """A catalog genome records a GFF that is not in the local cache."""


def _dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, separators=(",", ":")))


def build_index(out_dir: Path, sources: list, strict: bool = False) -> list:
    """Write ``<genome>.json`` shards, ``manifest.json`` and ``names.json`` into ``out_dir``.

    Returns the manifest. A genome whose GFF is not cached is recorded with status "missing"
    (or raises MissingGffError when ``strict``); one with no genes has status "empty".
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest, names = [], []
    for index, source in enumerate(sources):
        entry = {
            "genome": source.genome_id,
            "species": source.species,
            "strain": source.strain,
            "aliases": list(source.aliases),
            "genes": 0,
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
        if not genes:
            entry["status"] = "empty"
        _dump(out_dir / f"{source.genome_id}.json", [g.to_dict() for g in genes])
        names.extend([index, g.id, g.name, g.product] for g in genes)
        manifest.append(entry)
    _dump(out_dir / "manifest.json", manifest)
    _dump(out_dir / "names.json", names)
    return manifest
