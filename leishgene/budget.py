"""Keep the website data small enough to load in a browser."""
import gzip
from pathlib import Path

MAX_SHARD_BYTES = 5_000_000
MAX_NAMES_BYTES = 5_000_000


def _gzipped_size(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), compresslevel=6))


def check_budget(
    site_data_dir: Path, max_shard_bytes: int = MAX_SHARD_BYTES, max_names_bytes: int = MAX_NAMES_BYTES
) -> list:
    """One message per file over budget. Sizes are gzipped, which is what GitHub Pages serves."""
    messages = []
    for path in sorted(Path(site_data_dir).glob("*.json")):
        if path.name == "manifest.json":
            continue
        limit = max_names_bytes if path.name == "names.json" else max_shard_bytes
        size = _gzipped_size(path)
        if size > limit:
            messages.append(f"{path.name}: {size / 1e6:.1f} MB gzipped exceeds the {limit / 1e6:.1f} MB budget")
    return messages
