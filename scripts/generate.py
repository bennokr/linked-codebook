"""Generate the JSON Schema, the types of both libraries and their constants from spec/*.yaml."""

import json
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
        "schema": schema,
    }


def main() -> None:
    schema = run("gen-json-schema", "--no-include-null", "spec/profile.yaml")
    # The top level is the Profile class; point to it instead of repeating it.
    parsed = json.loads(schema)
    root = {key: parsed[key] for key in ("$schema", "$id", "$defs")} | {"$ref": "#/$defs/Profile"}
    (SPEC / "generated").mkdir(exist_ok=True)
    (SPEC / "generated/profile.schema.json").write_text(json.dumps(root, indent=2) + "\n")
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
    # PEP 728 `closed=True` needs Python 3.15; the types are the same without it.
    types = PY_GENERATED / "types.py"
    types.write_text(types.read_text().replace(", closed=True", ""))


if __name__ == "__main__":
    main()
