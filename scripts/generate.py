"""Generate the JSON Schema, the types of both libraries and their constants from spec/*.yaml."""

import ast
import inspect
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
        "language": load("language"),
        "enums": enums,
        "vocabulary": load("vocabulary"),
        "commands": load("commands"),
        "frictionless": load("frictionless"),
        "redcap": load("redcap"),
        "table": load("table"),
        "condition": load("condition"),
        "readstat": load("readstat"),
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


def fill_block(page: Path, name: str, body: str) -> None:
    """Replace what lies between `<!-- name: ... -->` and `<!-- /name -->` in a page."""
    pattern = rf"(<!-- {re.escape(name)}:.*?-->\n).*?(<!-- /{re.escape(name)} -->)"
    page.write_text(re.sub(pattern, lambda m: f"{m[1]}{body}\n{m[2]}", page.read_text(), flags=re.DOTALL))


DOCS_URL = "https://bennokr.github.io/linked-codebook/docs/"


def section_anchors() -> dict[str, str]:
    """The anchor of each numbered section of the specification, slugged as the documentation site does."""
    anchors = {}
    for line in (ROOT / "docs/specification.md").read_text().splitlines():
        match = re.match(r"#{2,3} (\d+(?:\.\d+)?)\.? (.+)", line)
        if match:
            anchors[match[1]] = re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", line.lstrip("# ").strip().lower()))
    return anchors


def cell(doc: str, anchors: dict[str, str]) -> str:
    """A docstring as one table cell: paragraphs joined, links to the documentation made relative."""
    text = " ".join(doc.split())
    text = re.sub(rf"\]\({re.escape(DOCS_URL)}([a-z-]+)\)", r"](\1.md)", text)
    text = re.sub(
        r"section (\d+(?:\.\d+)?) of the specification",
        lambda match: f"[{match[0]}](specification.md#{anchors[match[1]]})",
        text,
    )
    return text.replace("|", "\\|")


def python_signature(name: str, args: ast.arguments) -> str:
    """The parameters of a function as they are written in a call, without annotations."""

    def default(node: ast.expr) -> str:
        return (
            json.dumps(node.value)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            else ast.unparse(node)
        )

    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    parts = [a.arg + (f"={default(d)}" if d else "") for a, d in zip(positional, defaults, strict=True)]
    if args.kwonlyargs:
        parts.append("*")
        parts += [
            a.arg + (f"={default(d)}" if d else "") for a, d in zip(args.kwonlyargs, args.kw_defaults, strict=True)
        ]
    return f"{name}({', '.join(parts)})"


def docstring_after(body: list[ast.stmt], index: int) -> str:
    """The string that follows a module-level assignment, as a docstring of the name."""
    follower = body[index + 1] if index + 1 < len(body) else None
    if (
        isinstance(follower, ast.Expr)
        and isinstance(follower.value, ast.Constant)
        and isinstance(follower.value.value, str)
    ):
        return inspect.cleandoc(follower.value.value)
    return ""


def python_api() -> list[dict[str, str]]:
    """The exports of the Python package with their docstrings, found by reading the source, not by importing it."""
    init = ast.parse((PY_GENERATED / "__init__.py").read_text())
    names = next(
        ast.literal_eval(node.value)
        for node in init.body
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "__all__"
    )
    origin = {
        (alias.asname or alias.name): (node.module, alias.name)
        for node in init.body
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
    }
    api = []
    for name in sorted(names, key=str.lower):
        module, original = origin[name]
        body = ast.parse((PY_GENERATED / f"{module}.py").read_text()).body
        for index, node in enumerate(body):
            if isinstance(node, ast.FunctionDef) and node.name == original:
                api.append(
                    {
                        "name": name,
                        "kind": "function",
                        "signature": python_signature(name, node.args),
                        "doc": ast.get_docstring(node) or "",
                    }
                )
            elif isinstance(node, ast.ClassDef) and node.name == original:
                fields = ", ".join(
                    f"{ast.unparse(f.target)}: {ast.unparse(f.annotation)}"
                    for f in node.body
                    if isinstance(f, ast.AnnAssign)
                )
                api.append(
                    {
                        "name": name,
                        "kind": "type",
                        "definition": f"NamedTuple({fields})",
                        "doc": ast.get_docstring(node) or "",
                    }
                )
            elif isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == original:
                api.append(
                    {
                        "name": name,
                        "kind": "type",
                        "definition": ast.unparse(node.value),
                        "doc": docstring_after(body, index),
                    }
                )
            elif isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == original:
                api.append({"name": name, "kind": "constant", "signature": name, "doc": docstring_after(body, index)})
    return api


def camel(name: str) -> str:
    return re.sub(r"_([a-z])", lambda match: match[1].upper(), name.lower())


def check_api(python: list[dict[str, str]], typescript: list[dict[str, str]]) -> None:
    """Fails if an export has no description, or if the two libraries do not export the same names."""
    missing = [
        f"{lang}: {entry['name']}"
        for lang, api in (("Python", python), ("TypeScript", typescript))
        for entry in api
        if not entry["doc"]
    ]
    if missing:
        message = f"These exports have no docstring or TSDoc: {', '.join(missing)}"
        raise SystemExit(message)
    values = {entry["name"] for entry in typescript if entry["kind"] != "type"}
    mapped = {camel(entry["name"]) for entry in python if entry["kind"] != "type"}
    types = {entry["name"] for entry in typescript if entry["kind"] == "type"}
    only_python = sorted(entry["name"] for entry in python if entry["kind"] == "type" and entry["name"] not in types)
    if values != mapped or only_python:
        message = (
            f"The libraries export different names. Only in Python: {sorted(mapped - values) + only_python}; "
            f"only in TypeScript: {sorted(values - mapped)}"
        )
        raise SystemExit(message)


def function_table(api: list[dict[str, str]], anchors: dict[str, str]) -> str:
    rows = [f"| `{e['signature']}` | {cell(e['doc'], anchors)} |" for e in api if e["kind"] != "type"]
    return "\n".join(["| Function | Description |", "| --- | --- |", *rows])


def type_table(api: list[dict[str, str]], anchors: dict[str, str]) -> str:
    rows = [
        f"| `{e['name']}` | `{e['definition'].replace('|', chr(92) + '|')}` | {cell(e['doc'], anchors)} |"
        for e in api
        if e["kind"] == "type"
    ]
    return "\n".join(["| Name | Definition | Description |", "| --- | --- | --- |", *rows])


def import_block(api: list[dict[str, str]], language: str) -> str:
    """The import statement that lists every export, in the layout of the formatter of the language."""
    if language == "python":
        order = {"function": 0, "type": 1, "constant": 2}
        names = [e["name"] for e in sorted(api, key=lambda e: order[e["kind"]])]
        body = "\n".join(f"    {name}," for name in names)
        return f"```python\nfrom linked_codebook import (\n{body}\n)\n```"
    names = sorted((e["name"] for e in api if e["kind"] != "type"), key=str.lower)
    body = "\n".join(f"  {name}," for name in names)
    return f"```ts\nimport {{\n{body}\n}} from 'linked-codebook';\n```"


def api_pages() -> None:
    """Write the tables of exports of the Python and TypeScript pages from the docstrings and the TSDoc."""
    python = python_api()
    typescript = sorted(json.loads(run("node", "scripts/api.ts")), key=lambda entry: entry["name"].lower())
    check_api(python, typescript)
    anchors = section_anchors()
    for page, api, language in (("python", python, "python"), ("typescript", typescript, "ts")):
        path = ROOT / f"docs/{page}.md"
        fill_block(path, "api-imports", import_block(api, language))
        fill_block(path, "api", function_table(api, anchors))
        fill_block(path, "api-types", type_table(api, anchors))


def main() -> None:
    schema = run("gen-json-schema", "--no-include-null", "spec/profile.yaml")
    # The top level is the Profile class; point to it instead of repeating it.
    parsed = json.loads(schema)
    root = {key: parsed[key] for key in ("$schema", "$id", "$defs")} | {"$ref": "#/$defs/Profile"}
    (SPEC / "generated").mkdir(exist_ok=True)
    (SPEC / "generated/profile.schema.json").write_text(json.dumps(root, indent=2) + "\n")
    (ROOT / "docs/data-model.md").write_text(model_page(load("profile")))
    (ROOT / "docs/vocabulary.md").write_text(vocabulary_page(load("vocabulary")))
    fill_block(ROOT / "docs/cli.md", "commands", command_table(load("commands")))
    rules = (SPEC / "inference.yaml").read_text().rstrip("\n")
    fill_block(ROOT / "docs/type-profiling.md", "inference.yaml", f"```yaml\n{rules}\n```")
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
    api_pages()


if __name__ == "__main__":
    main()
