"""Check every term the profile uses against its published vocabulary and write spec/vocabulary.yaml.

Needs network access. Terms that a vocabulary does not define are listed under `unverified`;
the conformance tests fail while that list is not empty.
"""

import re
import urllib.request
from datetime import date
from pathlib import Path

import yaml
from rdflib import RDF, Graph

SPEC = Path(__file__).resolve().parent.parent / "spec"
FORMATS = {"widoco": "text/html", "xml": "application/rdf+xml", "turtle": "text/turtle"}


def curies(value: object) -> set[str]:
    """All prefixed names in a nested YAML value, from strings like dsv:Column or {"@id": dsv:Column}."""
    if isinstance(value, str):
        return {value} if re.fullmatch(r"[a-z]+:[A-Za-z]+", value) else set()
    items = value.values() if isinstance(value, dict) else value if isinstance(value, list) else []
    return set().union(*(curies(item) for item in items)) if items else set()


def used_terms(jsonld: dict, profile: dict) -> set[str]:
    meanings = [meta["meaning"] for enum in profile["enums"].values() for meta in enum["permissible_values"].values() if meta]
    keys = ("terms", "types", "node_keys", "accepted")
    return curies([jsonld[key] for key in keys]) | set(meanings)


def fetch(url: str, kind: str) -> str:
    request = urllib.request.Request(url, headers={"Accept": FORMATS[kind], "User-Agent": "linked-codebook"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read().decode()


def kinds(source: dict, namespace: str) -> dict[str, str]:
    """Map each term defined by a vocabulary to the kind of thing it is."""
    text = fetch(source["url"], source["format"])
    if source["format"] == "widoco":
        found = re.finditer(r'id="([A-Za-z]+)"[^>]*>(?:(?!id=").){0,400}?(Class|Object Property|Data Property)\s+ToC', text, re.S)
        return {match[1]: match[2] for match in found}
    graph = Graph().parse(data=text, format=source["format"])
    return {
        str(subject)[len(namespace):]: str(next(graph.objects(subject, RDF.type), "")).rsplit("#", 1)[-1]
        for subject in set(graph.subjects(RDF.type, None))
        if str(subject).startswith(namespace)
    }


def main() -> None:
    jsonld = yaml.safe_load((SPEC / "jsonld.yaml").read_text())
    profile = yaml.safe_load((SPEC / "profile.yaml").read_text())
    wanted: dict[str, list[str]] = {}
    for term in sorted(used_terms(jsonld, profile)):
        prefix, local = term.split(":")
        wanted.setdefault(prefix, []).append(local)
    result: dict = {"pinned_on": date.today().isoformat(), "vocabularies": {}, "unverified": []}
    for prefix, locals_ in wanted.items():
        namespace = jsonld["prefixes"][prefix]
        found = kinds(jsonld["sources"][prefix], namespace)
        result["vocabularies"][prefix] = {
            "namespace": namespace,
            "source": jsonld["sources"][prefix]["url"],
            "terms": {local: found[local] for local in locals_ if local in found},
        }
        result["unverified"] += [f"{prefix}:{local}" for local in locals_ if local not in found]
    (SPEC / "vocabulary.yaml").write_text(yaml.safe_dump(result, sort_keys=True, width=120))


if __name__ == "__main__":
    main()
