"""Read, write and check codebooks of tables whose variables are linked to concepts."""

from .canonical import canonical
from .cli import Result, run
from .condition import evaluate as evaluate_condition
from .condition import parse_condition
from .constants import TABLE as TABLE_SPEC
from .frictionless import to_frictionless
from .infer import Detector, infer, infer_column, infer_language, is_identifier_name, is_numeric, observe
from .jsonld import build
from .merge import merge
from .missingness import conditions, missingness
from .read import parse
from .readstat import from_readstat
from .redcap import from_redcap
from .sssom import from_sssom, to_sssom, unmatched_sssom
from .table import from_tables, table_warnings, to_tables
from .validate import validate

__all__ = [
    "TABLE_SPEC",
    "Detector",
    "Result",
    "build",
    "canonical",
    "conditions",
    "evaluate_condition",
    "from_readstat",
    "from_redcap",
    "from_sssom",
    "from_tables",
    "infer",
    "infer_column",
    "infer_language",
    "is_identifier_name",
    "is_numeric",
    "merge",
    "missingness",
    "observe",
    "parse",
    "parse_condition",
    "run",
    "table_warnings",
    "to_frictionless",
    "to_sssom",
    "to_tables",
    "unmatched_sssom",
    "validate",
]
