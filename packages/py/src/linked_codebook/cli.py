"""The command line, as a function that does no input or output."""

import json
from collections.abc import Callable
from typing import NamedTuple, cast

from .canonical import canonical
from .condition import parse_condition
from .constants import COMMANDS as SPEC
from .frictionless import to_frictionless
from .infer import infer
from .jsonld import build
from .merge import merge
from .missingness import conditions, missingness
from .read import parse
from .readstat import from_readstat
from .redcap import from_redcap
from .sssom import from_sssom, to_sssom
from .table import from_tables, table_warnings, to_tables
from .types import Profile
from .validate import validate


class Result(NamedTuple):
    """What `run` returns: the output text and the exit code."""

    stdout: str
    code: int


def done(stdout: str) -> Result:
    return Result(stdout, 0)


def load(text: str) -> Profile:
    """A profile, read from profile JSON or from DSV JSON-LD."""
    document = json.loads(text)
    linked = any(key.startswith("@") for key in document) or "datasetSchema" in document
    return parse(document) if linked else cast("Profile", document)


def check(text: str) -> Result:
    errors = validate(json.loads(text))
    return Result("".join(f"{error}\n" for error in errors) if errors else "ok\n", 1 if errors else 0)


COMMANDS: dict[str, Callable[..., Result]] = {
    "normalize": lambda profile: done(canonical(load(profile))),
    "build": lambda profile: done(canonical(build(load(profile)))),
    "parse-condition": lambda text: done(canonical(parse_condition(text))),
    "conditions": lambda profile: done(canonical(conditions(load(profile)))),
    "missingness": lambda profile, data: done(canonical(missingness(load(profile), json.loads(data)))),
    "from-readstat": lambda variables: done(canonical(from_readstat(json.loads(variables)))),
    "from-redcap": lambda dictionary: done(canonical(from_redcap(dictionary))),
    "from-tables": lambda tables: done(canonical(from_tables(json.loads(tables)))),
    "to-tables": lambda profile: done(canonical(to_tables(load(profile)))),
    "check-tables": lambda tables: done("".join(f"{w}\n" for w in table_warnings(json.loads(tables))) or "ok\n"),
    "to-frictionless": lambda profile: done(canonical(to_frictionless(load(profile)))),
    "to-sssom": lambda profile: done(to_sssom(load(profile))),
    "from-sssom": lambda sssom, profile: done(canonical(from_sssom(sssom, load(profile)))),
    "merge": lambda base, incoming: done(canonical(merge(load(base), load(incoming)))),
    "infer": lambda data: done(canonical(infer(json.loads(data)))),
    "validate": check,
}

USAGE = "usage: linked-codebook <command> <file>...\n\n" + "".join(
    f"  {' '.join([name, *(f'<{file}>' for file in entry['files'])])}\n      {entry['summary']}\n"
    for name, entry in SPEC.items()
)


def run(args: list[str], texts: dict[str, str]) -> Result:
    """The command line as a function: runs a command on the texts of the files it names.

    It returns `(stdout, code)` and does no input or output itself. See [Command
    line](https://bennokr.github.io/linked-codebook/docs/cli).
    """
    name, *files = args or [""]
    command = COMMANDS.get(name)
    if command is None or len(SPEC[name]["files"]) != len(files):
        return Result(USAGE, 2)
    try:
        missing = next((file for file in files if file not in texts), None)
        if missing is not None:
            message = f"no such file: {missing}"
            raise FileNotFoundError(message)  # noqa: TRY301
        return command(*(texts[file] for file in files))
    except Exception as error:  # noqa: BLE001
        return Result(f"error: {error}\n", 2)
