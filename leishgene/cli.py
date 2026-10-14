"""Command line interface: build the index, search it, export it for the website."""
import json
import logging
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from leishgene.budget import check_budget
from leishgene.export import SiteIndexError, export_site, load_manifest
from leishgene.index import MissingGffError, build_index
from leishgene.search import QueryError, parse_query
from leishgene.sources import list_sources, load_overrides
from leishgene.table import OUTPUT_SUFFIXES, write_table

DEFAULT_INDEX = Path.home() / ".cache" / "leishgene"
DEFAULT_OVERRIDES = Path("data/extra/gff_overrides.yaml")

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
@click.option(
    "--overrides",
    type=click.Path(path_type=Path),
    default=DEFAULT_OVERRIDES,
    show_default=True,
    help="YAML of GFFs that replace or complete the catalog (used when the file exists)",
)
def build(index_dir, strict, overrides):
    """Parse the cached GFFs of every catalog genome that has one and write the index."""
    try:
        sources = list_sources(overrides=load_overrides(overrides) if overrides.is_file() else None)
        manifest = build_index(index_dir, sources, strict=strict)
    except (MissingGffError, ValueError, FileNotFoundError) as exc:
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
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Also write every match (not only --limit rows) to a .tsv, .csv or .bed file",
)
def search(query, index_dir, limit, output):
    """Find genes matching QUERY (words are AND-ed; `*` glob, `/regex/`, `field:value`, "phrases")."""
    try:
        parsed = parse_query(query)
    except QueryError as exc:
        raise click.UsageError(str(exc))
    if not parsed.terms:
        click.echo("Empty query: nothing to search.")
        return
    if output is not None and output.suffix not in OUTPUT_SUFFIXES:
        raise click.UsageError(f"--output must end in .tsv, .csv or .bed, not {output.suffix or output.name!r}")
    manifest = _load_manifest(index_dir)
    hits, total, matched = [], 0, []
    for entry in manifest:
        if entry["status"] != "ok":
            continue
        for gene in json.loads((Path(index_dir) / f"{entry['genome']}.json").read_text()):
            gene.update(species=entry["species"] or "", strain=entry["strain"] or "", aliases=entry["aliases"])
            if parsed.matches(gene):
                total += 1
                if len(hits) < limit:
                    hits.append(gene)
                if output is not None:
                    matched.append(gene)
    table = Table(title=f"{total} match(es)" + (f", showing {limit}" if total > limit else ""))
    for column in ("genome", "strain", "location", "length", "strand", "id", "type", "product"):
        table.add_column(column)
    for g in hits:
        cells = (
            g["genome"],
            g.get("strain", ""),
            f"{g['seqid']}:{g['start']}-{g['end']}",
            f"{g['end'] - g['start'] + 1:,} bp",
            g["strand"],
            g["id"],
            g["type"],
            g["product"],
        )
        table.add_row(*(Text(str(c)) for c in cells))  # Text: product names contain [brackets], not Rich markup
    Console().print(table)
    if output is not None:
        write_table(matched, output)
        click.echo(f"wrote {total} row(s) to {output}")


@cli.command()
@index_option
@click.option("--list-gff-genomes", is_flag=True, help="Print the catalog ids of genomes that have a GFF, one per line")
def info(index_dir, list_gff_genomes):
    """Show the genomes of an index, and those whose GFF was missing."""
    if list_gff_genomes:
        for source in list_sources():
            click.echo(source.genome_id)
        return
    manifest = _load_manifest(index_dir)
    table = Table()
    for column in ("genome", "species", "genes", "status"):
        table.add_column(column)
    for e in manifest:
        table.add_row(*(Text(c) for c in (e["genome"], e["species"] or "", str(e["genes"]), e["status"])))
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
    problems = check_budget(output)
    if problems:
        raise click.ClickException("size budget exceeded:\n" + "\n".join(problems))
