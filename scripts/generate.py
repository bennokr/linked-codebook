"""Generate the JSON Schema, the types of both libraries and their constants from spec/*.yaml."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec"
TS_GENERATED = ROOT / "packages/ts/src/generated"
PY_GENERATED = ROOT / "packages/py/src/linked_codebook"


def load(name: str) -> dict[str, Any]:
    return dict(yaml.safe_load((SPEC / f"{name}.yaml").read_text()))


def run(*command: str) -> str:
    return str(subprocess.run(command, check=True, capture_output=True, text=True, cwd=ROOT).stdout)


def constants() -> dict[str, Any]:
    profile, jsonld = load("profile"), load("jsonld")
    enums = {
        name: {value: (meta or {}).get("meaning") for value, meta in enum["permissible_values"].items()}
        for name, enum in profile["enums"].items()
    }
    jsonld.pop("sources")
    context = {**jsonld["prefixes"], **jsonld["terms"]}
    schema = json.loads((SPEC / "generated/profile.schema.json").read_text())
    return {
        "jsonld": {**jsonld, "context": context},
        "sssom": load("sssom"),
        "inference": load("inference"),
        "enums": enums,
        "vocabulary": load("vocabulary"),
        "commands": load("commands"),
        "frictionless": load("frictionless"),
        "redcap": load("redcap"),
        "schema": schema,
    }


def model_page(profile: dict[str, Any]) -> str:
    """The data model chapter of the specification, as Markdown."""
    lines = ["# Data model", "", "<!-- Generated from spec/profile.yaml by scripts/generate.py. Do not edit. -->", ""]
    for name, cls in profile["classes"].items():
        lines += [
            f"## {name}",
            "",
            cls["description"],
            "",
            "| Slot | Type | Required | Description |",
            "| --- | --- | --- | --- |",
        ]
        for slot in cls["slots"]:
            meta = profile["slots"][slot]
            kind = meta.get("range", profile["default_range"])
            kind = f"list of {kind}" if meta.get("multivalued") else kind
            required = "yes" if meta.get("required") else "no"
            lines.append(f"| `{slot}` | {kind} | {required} | {meta['description']} |")
        lines.append("")
    for name, enum in profile["enums"].items():
        lines += [f"## {name}", "", enum["description"], "", "| Value | Meaning |", "| --- | --- |"]
        lines += [
            f"| `{value}` | {(meta or {}).get('meaning', '')} |" for value, meta in enum["permissible_values"].items()
        ]
        lines.append("")
    return "\n".join(lines)


def command_table(commands: dict[str, Any]) -> str:
    """The table of commands of the command line page, as Markdown."""
    lines = ["| Command | Files | Result |", "| --- | --- | --- |"]
    lines += [f"| `{name}` | {', '.join(entry['files'])} | {entry['summary']} |" for name, entry in commands.items()]
    return "\n".join(lines)


def vocabulary_page(vocabulary: dict[str, Any]) -> str:
    """The list of the terms that the JSON-LD form uses, as Markdown."""
    lines = [
        "# Vocabulary",
        "",
        "<!-- Generated from spec/vocabulary.yaml by scripts/generate.py. Do not edit. -->",
        "",
    ]
    lines += [f"Every term below was found in its published vocabulary on {vocabulary['pinned_on']}.", ""]
    for prefix, entry in vocabulary["vocabularies"].items():
        terms = ", ".join(f"`{prefix}:{term}`" for term in entry["terms"])
        lines += [
            f"## `{prefix}`",
            "",
            f"Namespace: `{entry['namespace']}`. Source: <{entry['source']}>.",
            "",
            terms,
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    schema = run("gen-json-schema", "--no-include-null", "spec/profile.yaml")
    # The top level is the Profile class; point to it instead of repeating it.
    parsed = json.loads(schema)
    root = {key: parsed[key] for key in ("$schema", "$id", "$defs")} | {"$ref": "#/$defs/Profile"}
    (SPEC / "generated").mkdir(exist_ok=True)
    (SPEC / "generated/profile.schema.json").write_text(json.dumps(root, indent=2) + "\n")
    (ROOT / "docs/data-model.md").write_text(model_page(load("profile")))
    (ROOT / "docs/vocabulary.md").write_text(vocabulary_page(load("vocabulary")))
    cli = ROOT / "docs/cli.md"
    table = command_table(load("commands"))
    cli.write_text(
        re.sub(
            r"(<!-- commands:.*?-->\n).*?(<!-- /commands -->)",
            lambda m: f"{m[1]}{table}\n{m[2]}",
            cli.read_text(),
            flags=re.DOTALL,
        )
    )
    text = json.dumps(constants(), indent=2, sort_keys=True) + "\n"
    for target in (TS_GENERATED, PY_GENERATED):
        target.mkdir(parents=True, exist_ok=True)
        (target / "constants.json").write_text(text)
    run(
        "npx",
        "json2ts",
        "-i",
        "spec/generated/profile.schema.json",
        "-o",
        "packages/ts/src/generated/types.ts",
        "--format=false",
    )
    run(
        "datamodel-codegen",
        "--input",
        "spec/generated/profile.schema.json",
        "--input-file-type",
        "jsonschema",
        "--output-model-type",
        "typing.TypedDict",
        "--target-python-version",
        "3.11",
        "--output",
        "packages/py/src/linked_codebook/types.py",
        "--disable-timestamp",
    )
    # PEP 728 `closed=True` needs typing_extensions and Python 3.15; the types are the same without it.
    types = PY_GENERATED / "types.py"
    text = types.read_text().replace(", closed=True", "").replace("\n\nfrom typing_extensions import TypedDict", "")
    types.write_text(text.replace("TypeAlias\n", "TypeAlias, TypedDict\n", 1))


if __name__ == "__main__":
    main()
