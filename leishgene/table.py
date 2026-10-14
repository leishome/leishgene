"""Write search hits as a TSV or CSV table (same columns as the website export, web/export.js)."""
import csv
from pathlib import Path

COLUMNS = (
    "genome",
    "species",
    "strain",
    "seqid",
    "start",
    "end",
    "length",
    "strand",
    "id",
    "name",
    "type",
    "product",
    "ec",
    "go",
    "dbxref",
    "uniprot",
)
LIST_COLUMNS = {"ec", "go", "dbxref"}
DELIMITERS = {".tsv": "\t", ".csv": ","}


def uniprot_accessions(gene: dict) -> list:
    """Accessions of the UniProtKB/TrEMBL and UniProtKB/Swiss-Prot Dbxref values, once each."""
    out = []
    for ref in gene.get("dbxref") or []:
        if ref.startswith("UniProtKB/"):
            accession = ref.split(":", 1)[1] if ":" in ref else ""
            if accession and accession not in out:
                out.append(accession)
    return out


def _cell(gene: dict, column: str) -> str:
    if column == "length":
        return str(gene["end"] - gene["start"] + 1) if "start" in gene and "end" in gene else ""
    if column == "uniprot":
        return ";".join(uniprot_accessions(gene))
    value = gene.get(column)
    if value is None:
        return ""
    return ";".join(map(str, value)) if column in LIST_COLUMNS else str(value)


def write_table(genes, path) -> None:
    """Write ``genes`` to ``path``; the format follows the extension (.tsv or .csv)."""
    path = Path(path)
    if path.suffix not in DELIMITERS:
        raise ValueError(f"unsupported output extension {path.suffix or path.name!r}: use .tsv or .csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=DELIMITERS[path.suffix], lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows([_cell(g, c) for c in COLUMNS] for g in genes)
