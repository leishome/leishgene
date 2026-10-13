import json
from pathlib import Path

import pytest

from leishgene.search import QueryError, parse_query, search

CASES = json.loads((Path(__file__).parent / "query_cases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=[c["query"] for c in CASES])
def test_shared_vectors(case):
    if case.get("error"):
        with pytest.raises(QueryError):
            parse_query(case["query"])
    else:
        assert parse_query(case["query"]).matches(case["gene"]) is case["match"]


def test_empty_query_returns_nothing():
    assert search([{"id": "a"}], "   ") == []


def test_filters_only_query_allowed():
    genes = [{"id": "a", "type": "tRNA"}, {"id": "b", "type": "gene"}]
    assert [g["id"] for g in search(genes, "type:tRNA")] == ["a"]


def test_invalid_regex_raises_query_error_with_message():
    with pytest.raises(QueryError, match="invalid regular expression"):
        parse_query("/(/")
