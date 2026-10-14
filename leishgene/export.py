"""Validate a built index and copy it into the website's data directory."""
import json
import shutil
from pathlib import Path


class SiteIndexError(RuntimeError):
    """The index directory is missing files or is inconsistent."""


def load_manifest(index_dir: Path) -> list:
    path = Path(index_dir) / "manifest.json"
    if not path.is_file():
        raise SiteIndexError(f"no index in {index_dir}: run `leishgene build` first")
    return json.loads(path.read_text())


def validate_index(index_dir: Path) -> list:
    index_dir = Path(index_dir)
    manifest = load_manifest(index_dir)
    names = index_dir / "names.json"
    if not names.is_file():
        raise SiteIndexError(f"{names} is missing: run `leishgene build` again")
    for entry in manifest:
        if entry["status"] != "missing" and not (index_dir / f"{entry['genome']}.json").is_file():
            raise SiteIndexError(f"{entry['genome']}: shard {entry['genome']}.json is missing")
    return manifest


def export_site(index_dir: Path, site_data_dir: Path) -> None:
    """Copy manifest, names and the shards of every genome that has one into ``site_data_dir``."""
    manifest = validate_index(index_dir)
    index_dir, site_data_dir = Path(index_dir), Path(site_data_dir)
    site_data_dir.mkdir(parents=True, exist_ok=True)
    wanted = ["manifest.json", "names.json"] + [f"{e['genome']}.json" for e in manifest if e["status"] != "missing"]
    if (index_dir / "seqlens.json").is_file():  # absent from indexes built before the position plot
        wanted.append("seqlens.json")
    for name in wanted:
        shutil.copyfile(index_dir / name, site_data_dir / name)
