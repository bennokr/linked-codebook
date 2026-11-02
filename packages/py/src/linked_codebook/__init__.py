"""Read, write and check codebooks of tables whose variables are linked to concepts."""

from .canonical import canonical
from .cli import Result, run
from .constants import TABLE as TABLE_SPEC
from .frictionless import to_frictionless
from .infer import infer, infer_column, is_numeric, observe
from .jsonld import build
from .merge import merge
from .read import parse
from .redcap import from_redcap
from .sssom import from_sssom, to_sssom, unmatched_sssom
from .table import from_tables, table_warnings, to_tables
from .validate import validate

__all__ = [
    "TABLE_SPEC",
    "Result",
    "build",
    "canonical",
    "from_redcap",
    "from_sssom",
    "from_tables",
    "infer",
    "infer_column",
    "is_numeric",
    "merge",
    "observe",
    "parse",
    "run",
    "table_warnings",
    "to_frictionless",
    "to_sssom",
    "to_tables",
    "unmatched_sssom",
    "validate",
]
