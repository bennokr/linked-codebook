"""Read, write and check codebooks of tables whose variables are linked to concepts."""

from .canonical import canonical
from .cli import Result, run
from .frictionless import to_frictionless
from .infer import infer, infer_column, is_numeric, observe
from .jsonld import build
from .merge import merge
from .read import parse
from .sssom import from_sssom, to_sssom, unmatched_sssom
from .validate import validate

__all__ = [
    "Result",
    "build",
    "canonical",
    "from_sssom",
    "infer",
    "infer_column",
    "is_numeric",
    "merge",
    "observe",
    "parse",
    "run",
    "to_frictionless",
    "to_sssom",
    "unmatched_sssom",
    "validate",
]
