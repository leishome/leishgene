"""Command line interface: build the index, search it, export it for the website."""
import json
import logging
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.table import Table

from leishgene.export import SiteIndexError, export_site, load_manifest
from leishgene.index import MissingGffError, build_index
from leishgene.search import QueryError, parse_query
from leishgene.sources import list_sources

DEFAULT_INDEX = Path.home() / ".cache" / "leishgene"

index_option = click.option(
    "-i",
    "--index-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_INDEX,
    show_default=True,
    help="Index directory",
)


@click.group()
def cli():
    """Search genes and annotations across Leishmania genomes of the leishref catalog."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


@cli.command()
@index_option
@click.option("--strict", is_flag=True, help="Fail when a catalog GFF is not in the local cache")
def build(index_dir, strict):
    """Parse the cached GFFs of every catalog genome that has one and write the index."""
    try:
        manifest = build_index(index_dir, list_sources(), strict=strict)
    except MissingGffError as exc:
        raise click.ClickException(str(exc))
    ok = [e for e in manifest if e["status"] == "ok"]
    click.echo(f"{len(ok)}/{len(manifest)} genomes, {sum(e['genes'] for e in ok)} genes -> {index_dir}")


def _load_manifest(index_dir):
    try:
        return load_manifest(index_dir)
    except SiteIndexError as exc:
        raise click.ClickException(str(exc))


@cli.command()
@click.argument("query")
@index_option
@click.option("--limit", default=50, show_default=True, help="Maximum rows to print")
def search(query, index_dir, limit):
    """Find genes matching QUERY (words are AND-ed; `*` glob, `/regex/`, `field:value`, "phrases")."""
    try:
        parsed = parse_query(query)
    except QueryError as exc:
        raise click.UsageError(str(exc))
    if not parsed.terms:
        click.echo("Empty query: nothing to search.")
        return
    manifest = _load_manifest(index_dir)
    hits, total = [], 0
    for entry in manifest:
        if entry["status"] != "ok":
            continue
        for gene in json.loads((Path(index_dir) / f"{entry['genome']}.json").read_text()):
            gene["species"] = entry["species"] or ""
            if parsed.matches(gene):
                total += 1
                if len(hits) < limit:
                    hits.append(gene)
    table = Table(title=f"{total} match(es)" + (f", showing {limit}" if total > limit else ""))
    for column in ("genome", "location", "strand", "id", "type", "product"):
        table.add_column(column)
    for g in hits:
        table.add_row(
            g["genome"], f"{g['seqid']}:{g['start']}-{g['end']}", g["strand"], g["id"], g["type"], g["product"]
        )
    Console().print(table)


@cli.command()
@index_option
def info(index_dir):
    """Show the genomes of an index, and those whose GFF was missing."""
    manifest = _load_manifest(index_dir)
    table = Table()
    for column in ("genome", "species", "genes", "status"):
        table.add_column(column)
    for e in manifest:
        table.add_row(e["genome"], e["species"] or "", str(e["genes"]), e["status"])
    Console().print(table)


@cli.command()
@index_option
@click.option("-o", "--output", type=click.Path(path_type=Path), default=Path("web/data"), show_default=True)
def export(index_dir, output):
    """Validate the index and copy it into the website data directory."""
    try:
        export_site(index_dir, output)
    except SiteIndexError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"exported -> {output}")
