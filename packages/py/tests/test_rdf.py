"""What the JSON-LD says once it is RDF: a key without an IRI is dropped by JSON-LD, so each one must have one."""

import json

from linked_codebook import build
from linked_codebook.types import Profile
from rdflib import Graph, URIRef

LC = "https://bennokr.github.io/linked-codebook/profile#"
CSVW = "http://www.w3.org/ns/csvw#"
PROFILE: Profile = {
    "identifier": "https://example.org/data/",
    "columns": [
        {"name": "age", "minimum": 18, "maximum": 100, "format": "0", "group": "demographics", "identifying": True},
        {
            "name": "cigs",
            "applies_when": "[smoker] == 'yes'",
            "missing_values": ["77"],
            "missing_range": {"low": 9000, "high": 9999},
            "closed": True,
        },
    ],
}


def predicates() -> dict[str, set[str]]:
    graph = Graph().parse(data=json.dumps(build(PROFILE)), format="json-ld")
    return {str(c): {str(p) for p in graph.predicates(c)} for c in graph.subjects(None, None)}


def test_every_slot_of_a_column_is_in_the_rdf() -> None:
    columns = predicates()
    age, cigs = columns["https://example.org/data/#column-age"], columns["https://example.org/data/#column-cigs"]
    assert {CSVW + "minInclusive", CSVW + "maxInclusive", CSVW + "format", LC + "group", LC + "identifying"} <= age
    assert {LC + "applies_when", LC + "closed", LC + "missing_range", CSVW + "null"} <= cigs


def test_a_missing_range_keeps_its_limits() -> None:
    graph = Graph().parse(data=json.dumps(build(PROFILE)), format="json-ld")
    (node,) = graph.objects(None, URIRef(LC + "missing_range"))
    limits = {str(p).rsplit("#", 1)[1]: int(str(o)) for p, o in graph.predicate_objects(node)}
    assert limits == {"minInclusive": 9000, "maxInclusive": 9999}
