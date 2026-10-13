"""Query grammar shared with web/query.js.

Terms are separated by whitespace and AND-ed. A term is a case-insensitive substring, a glob
(``*``), a regular expression (``/re/``) or a quoted phrase (``"two words"``). ``field:term``
restricts the term to one field; a ``word:`` prefix that is not a known field is part of the term
(so ``GO:0004672`` and ``GeneID:123`` search the annotation values).
"""
import re
from typing import Iterable

FIELDS = ("id", "name", "product", "type", "species", "genome", "ec", "go", "dbxref")
LIST_FIELDS = {"ec", "go", "dbxref"}
BARE_FIELDS = ("id", "name", "product", "ec", "go", "dbxref")

_TOKEN = re.compile(r'(?:(\w+):)?(?:"([^"]*)"|/((?:\\.|[^/\\])*)/|(\S+))')


class QueryError(ValueError):
    """The query text could not be parsed."""


def _compile(text: str) -> "re.Pattern":
    return re.compile(text, re.IGNORECASE)


def _term_pattern(quoted, regex, plain) -> "re.Pattern":
    if regex is not None:
        try:
            return _compile(regex)
        except re.error as exc:
            raise QueryError(f"invalid regular expression /{regex}/: {exc}")
    text = quoted if quoted is not None else plain
    return _compile(".*".join(re.escape(part) for part in text.split("*")))


def _values(gene: dict, field: str) -> list:
    value = gene.get(field)
    if value is None:
        return []
    return [str(v) for v in value] if field in LIST_FIELDS else [str(value)]


def _bare_values(gene: dict) -> list:
    out = []
    for field in BARE_FIELDS:
        out.extend(_values(gene, field))
    out.extend(str(v) for v in (gene.get("attrs") or {}).values())
    return out


class Query:
    def __init__(self, terms: list):
        self.terms = terms  # (field or None, compiled pattern)

    def matches(self, gene: dict) -> bool:
        for field, pattern in self.terms:
            values = _bare_values(gene) if field is None else _values(gene, field)
            if not any(pattern.search(v) for v in values):
                return False
        return True


def parse_query(text: str) -> Query:
    terms = []
    for match in _TOKEN.finditer(text):
        field, quoted, regex, plain = match.groups()
        if field is not None and field.lower() not in FIELDS:
            # not a filter: the prefix belongs to the term itself
            plain = f"{field}:{plain if plain is not None else quoted if quoted is not None else '/' + regex + '/'}"
            quoted = regex = None
            field = None
        terms.append((field.lower() if field else None, _term_pattern(quoted, regex, plain)))
    return Query(terms)


def search(genes: Iterable[dict], text: str) -> list:
    """Genes matching every term of ``text``; an empty query matches nothing."""
    query = parse_query(text)
    if not query.terms:
        return []
    return [g for g in genes if query.matches(g)]
