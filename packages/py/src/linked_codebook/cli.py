"""The command line, as a function that does no input or output."""

import json
from collections.abc import Callable
from typing import NamedTuple, cast

from .canonical import canonical
from .constants import COMMANDS as SPEC
from .frictionless import to_frictionless
from .infer import infer
from .jsonld import build
from .merge import merge
from .read import parse
from .sssom import from_sssom, to_sssom
from .types import Profile
from .validate import validate


class Result(NamedTuple):
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
    """Runs a command on the texts of the files it names. It does no input or output itself."""
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
