"""GFF3 parsing: one Gene record per gene, with its transcripts and CDS folded in."""
import gzip
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import unquote

GENE_TYPES = {"gene", "pseudogene", "ncRNA_gene", "protein_coding_gene"}
#: Feature rows that never become, or fold into, a searchable record.
IGNORED_TYPES = {
    "exon",
    "region",
    "intron",
    "five_prime_UTR",
    "three_prime_UTR",
    "start_codon",
    "stop_codon",
    "chromosome",
    "contig",
    "supercontig",
    "scaffold",
    "polypeptide",  # VEuPathDB: linked by Derives_from, nothing to search that the CDS does not hold
}
LIST_ATTRS = {"Dbxref": "dbxref", "Ontology_term": "go", "ec_number": "ec", "EC_number": "ec"}
PRODUCT_ATTRS = ("product", "description")
#: Attributes already held by a dedicated Gene field; not repeated in ``attrs``.
FIELD_ATTRS = {"ID", "Parent", "Name", *PRODUCT_ATTRS, *LIST_ATTRS}


@dataclass
class Gene:
    genome: str
    seqid: str
    start: int
    end: int
    strand: str
    type: str
    id: str
    name: str = ""
    product: str = ""
    ec: list = field(default_factory=list)
    go: list = field(default_factory=list)
    dbxref: list = field(default_factory=list)
    attrs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class _Row:
    seqid: str
    start: int
    end: int
    strand: str
    type: str
    attrs: dict  # decoded scalar values
    lists: dict  # list-valued attributes, split before decoding

    @property
    def id(self):
        return self.attrs.get("ID", "")

    @property
    def parent(self):
        return self.attrs.get("Parent", "")


def _open(path: Path):
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, encoding="utf-8")


def _parse_attributes(text: str):
    attrs, lists = {}, {}
    for item in text.strip().split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        attrs[key] = unquote(value)
        if key in LIST_ATTRS:
            lists[key] = [unquote(v) for v in value.split(",") if v]
    return attrs, lists


_QUOTED = re.compile(r'(\w+)="([^"]*)"')
_GO_FIELDS = ("BP", "MF", "CC")
_QUOTED_FOLDED = {"gene_id", "combinedAnnotation", "type", *_GO_FIELDS}


def _parse_quoted_attributes(text: str):
    """AUGUSTUS-style ``key="value"; ...`` attributes, mapped onto the GFF3 vocabulary.

    ``gene_id`` is the ID, ``combinedAnnotation`` the product and ``BP``/``MF``/``CC`` hold ``;``-separated
    GO terms (``NA`` when empty). ``type`` refines the column-3 type (pseudogene, snoRNA, ...) and is
    returned under ``type``. Empty values and ``transcript_id`` copies of the ID are dropped.
    """
    raw = dict(_QUOTED.findall(text))
    attrs = {"ID": raw.get("gene_id", ""), "type": raw.get("type", "")}
    if raw.get("combinedAnnotation"):
        attrs["product"] = raw["combinedAnnotation"]
    for key, value in raw.items():
        if key in _QUOTED_FOLDED or not value or (key == "transcript_id" and value == attrs["ID"]):
            continue
        attrs[key] = value
    go = [t for field_ in _GO_FIELDS for t in raw.get(field_, "").split(";") if t and t != "NA"]
    return attrs, {"Ontology_term": go} if go else {}


def _read_rows(path: Path, seqid_map=None) -> list:
    rows = []
    with _open(path) as handle:
        for line in handle:
            if line.startswith("##FASTA"):
                break
            if line.startswith("#") or not line.strip():
                continue
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 9:
                continue
            feature_type = cols[2]
            if '="' in cols[8]:
                attrs, lists = _parse_quoted_attributes(cols[8])
                feature_type = attrs.pop("type") or feature_type
            else:
                attrs, lists = _parse_attributes(cols[8])
            seqid = (seqid_map or {}).get(cols[0], cols[0])
            rows.append(_Row(seqid, int(cols[3]), int(cols[4]), cols[6], feature_type, attrs, lists))
    return rows


def _root(row: _Row, by_id: dict) -> _Row:
    """Top of the Parent chain: the gene for ordinary rows, the row itself for orphans."""
    seen = {id(row)}
    while row.parent and row.parent in by_id:
        nxt = by_id[row.parent]
        if id(nxt) in seen:
            break
        seen.add(id(nxt))
        row = nxt
    return row


def _build(genome: str, row: _Row, members: list) -> Gene:
    gene_level = row.type in GENE_TYPES
    ident = row.id
    if gene_level and ident.startswith("gene-"):
        ident = ident[len("gene-") :]
    # discontinuous features repeat the ID on several rows: one record spanning all of them
    parts = [row] + [m for m in members if m.type == row.type and m.id == row.id]
    gene = Gene(genome, row.seqid, min(p.start for p in parts), max(p.end for p in parts), row.strand, row.type, ident)
    for member in [row] + members:
        for key, value in member.attrs.items():
            if key not in FIELD_ATTRS:
                gene.attrs.setdefault(key, value)
        for key, target in LIST_ATTRS.items():
            for value in member.lists.get(key, []):
                if value not in getattr(gene, target):
                    getattr(gene, target).append(value)
        if not gene.product:
            gene.product = next((member.attrs[a] for a in PRODUCT_ATTRS if member.attrs.get(a)), "")
    gene.name = row.attrs.get("Name") or row.attrs.get("gene") or ident
    return gene


def parse_gff(path: Path, genome: str, seqid_map=None) -> list:
    """Parse a (possibly gzipped) GFF3 file into Gene records, in file order of their top-level rows.

    ``seqid_map`` renames sequences (GFF name -> name used by the genome's FASTA at the catalog).
    Rows with ``key="value"`` attributes (AUGUSTUS-style, see ``_parse_quoted_attributes``) are read too.

    Rows are grouped under the top of their Parent chain (the gene, or the mRNA/CDS of a gene-less
    annotation); rows that repeat an ID are merged into the first one.
    """
    rows = _read_rows(path, seqid_map)
    by_id: dict = {}
    for row in rows:
        if row.id:
            by_id.setdefault(row.id, row)
    members: dict = {}
    roots = []
    for row in rows:
        if row.type in IGNORED_TYPES:
            continue
        root = _root(row, by_id)
        if root is not row:
            members.setdefault(id(root), []).append(row)
        elif row.id and by_id[row.id] is not row:
            members.setdefault(id(by_id[row.id]), []).append(row)
        else:
            roots.append(row)
    return [_build(genome, r, members.get(id(r), [])) for r in roots]
