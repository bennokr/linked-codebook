"""Parsing and evaluating the conditions of skip logic, as defined by spec/condition.yaml."""

import re
from typing import Any

from .constants import CONDITION
from .infer import is_numeric

Condition = Any
Row = dict[str, Any]

TOKENS = [(token["kind"], re.compile(token["pattern"])) for token in CONDITION["tokens"]]
COMPARISONS = ["==", "!=", "<", "<=", ">", ">="]
KEYWORDS = ("and", "or", "not", "in", "is", "null")


def token_at(text: str, position: int) -> tuple[str, str]:
    for kind, pattern in TOKENS:
        match = pattern.match(text, position)
        if match:
            return kind, match.group()
    message = f"unexpected {text[position]!r} at position {position}"
    raise ValueError(message)


def tokenize(text: str) -> list[tuple[str, str]]:
    position, found = 0, []
    while position < len(text):
        kind, matched = token_at(text, position)
        position += len(matched)
        if kind != "space":
            found.append((kind, matched))
    return found


def unquote(text: str) -> str:
    quote = text[0]
    return text[1:-1].replace(quote * 2, quote)


def number(text: str) -> float:
    return float(text)


def variable(field: str) -> Condition:
    """The variable of a bracketed field: [name], or [name(code)] for an option of a REDCap checkbox."""
    content = field[1:-1].strip()
    option = re.fullmatch(r"([^()]+)\((.*)\)", content)
    if not option:
        return {"var": content}
    code = re.sub(CONDITION["checkbox_other"], "_", option[2].strip().lower())
    return {"var": CONDITION["checkbox"].format(name=option[1].strip(), code=code)}


def is_value(node: Condition) -> bool:
    return not isinstance(node, dict) or "var" in node


class Parser:
    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.at = 0

    def peek(self) -> tuple[str, str]:
        return self.tokens[self.at] if self.at < len(self.tokens) else ("end", "")

    def take(self) -> tuple[str, str]:
        token = self.peek()
        self.at += 1
        return token

    def is_word(self, *names: str) -> bool:
        kind, text = self.peek()
        return kind == "word" and text.lower() in names

    def is_join(self, name: str) -> bool:
        """True at the word `and` or `or`, or at a symbol that stands for it."""
        kind, text = self.peek()
        return self.is_word(name) or (kind == "join" and CONDITION["joins"][text] == name)

    def is_punct(self, text: str) -> bool:
        return self.peek() == ("punct", text)

    def expect(self, text: str) -> None:
        if not self.is_punct(text):
            message = f"expected {text!r}, found {self.peek()[1] or 'the end'!r}"
            raise ValueError(message)
        self.take()

    def parse(self) -> Condition:
        node = self.disjunction()
        if self.at < len(self.tokens):
            message = f"unexpected {self.peek()[1]!r}"
            raise ValueError(message)
        return node

    def chain(self, name: str, operand: Any) -> Condition:  # noqa: ANN401
        items = [operand()]
        while self.is_join(name):
            self.take()
            items.append(operand())
        return items[0] if len(items) == 1 else {name: items}

    def disjunction(self) -> Condition:
        return self.chain("or", self.conjunction)

    def conjunction(self) -> Condition:
        return self.chain("and", self.negation)

    def negation(self) -> Condition:
        if self.is_word("not"):
            self.take()
            return {"!": [self.negation()]}
        return self.comparison()

    def comparison(self) -> Condition:
        left = self.operand()
        kind, text = self.peek()
        if kind == "op":
            self.take()
            return compare(CONDITION["operators"][text], left, self.operand())
        if self.is_word("in"):
            self.take()
            return {"in": [left, self.options()]}
        if self.is_word("is"):
            self.take()
            return self.null_test(left)
        if is_value(left):
            message = "expected a comparison"
            raise ValueError(message)
        return left

    def null_test(self, left: Condition) -> Condition:
        negated = self.is_word("not")
        if negated:
            self.take()
        if not self.is_word("null"):
            message = "expected NULL"
            raise ValueError(message)
        self.take()
        test = {"null": [left]}
        return {"!": [test]} if negated else test

    def options(self) -> list[Condition]:
        self.expect("(")
        items = [self.literal()]
        while self.is_punct(","):
            self.take()
            items.append(self.literal())
        self.expect(")")
        return items

    def literal(self) -> Condition:
        kind, text = self.take()
        if kind == "number":
            return number(text)
        if kind == "string":
            return unquote(text)
        message = f"expected a value, found {text or 'the end'!r}"
        raise ValueError(message)

    def operand(self) -> Condition:
        kind, _ = self.peek()
        if kind in ("number", "string"):
            return self.literal()
        if self.is_punct("("):
            self.take()
            node = self.disjunction()
            self.expect(")")
            return node
        return self.name()

    def name(self) -> Condition:
        kind, text = self.take()
        if kind == "field":
            if self.peek()[0] == "field":
                message = "references to events are not supported"
                raise ValueError(message)
            return variable(text)
        if kind == "word" and text.lower() not in KEYWORDS:
            if self.is_punct("("):
                message = f"function {text} is not supported"
                raise ValueError(message)
            return {"var": text}
        message = f"expected a field or a value, found {text or 'the end'!r}"
        raise ValueError(message)


def compare(operator: str, left: Condition, right: Condition) -> Condition:
    """A comparison; comparing with the empty string asks whether the value is blank."""
    if right == "" and operator in ("==", "!="):
        test = {"null": [left]}
        return test if operator == "==" else {"!": [test]}
    return {operator: [left, right]}


def parse_condition(text: str) -> Condition:
    """Parses a condition of skip logic (REDCap branching logic or a SQL `WHERE` subset) into a tree.

    Raises `ValueError` for text that is not one, or that uses what the language does not have.
    """
    return Parser(tokenize(text)).parse()


def blank(cell: Any) -> bool:  # noqa: ANN401
    # None, empty text and a float NaN (how a data frame holds a missing number) are blank.
    return (
        cell is None or (isinstance(cell, str) and not cell.strip()) or (isinstance(cell, float) and cell != cell)  # noqa: PLR0124
    )


def value_of(node: Condition, row: Row) -> Any:  # noqa: ANN401
    if isinstance(node, dict) and "var" in node:
        cell = row.get(node["var"])
        return None if blank(cell) else cell
    return node


def same(left: Any, right: Any) -> bool:  # noqa: ANN401
    """Numbers are compared as numbers (so 1 and "1" are alike), everything else as text."""
    return float(left) == float(right) if is_numeric(left) and is_numeric(right) else str(left) == str(right)


def order(left: Any, right: Any) -> int:  # noqa: ANN401
    if is_numeric(left) and is_numeric(right):
        a, b = float(left), float(right)
    else:
        a, b = str(left), str(right)  # type: ignore[assignment]
    return (a > b) - (a < b)


def compared(operator: str, left: Any, right: Any, *, blank_is_value: bool) -> bool | None:  # noqa: ANN401
    if left is None or right is None:
        if blank_is_value and operator in ("==", "!="):
            return (left is None and right is None) == (operator == "==")
        return None
    if operator in ("==", "!="):
        return same(left, right) == (operator == "==")
    sign = order(left, right)
    return {"<": sign < 0, "<=": sign <= 0, ">": sign > 0, ">=": sign >= 0}[operator]


def all_of(results: list[bool | None]) -> bool | None:
    if False in results:
        return False
    return None if None in results else True


def any_of(results: list[bool | None]) -> bool | None:
    if True in results:
        return True
    return None if None in results else False


def evaluate(node: Condition, row: Row, *, blank: str = "value") -> bool | None:
    """Evaluates a condition tree for a row `{name: cell}`: True, False or None (unknown).

    `node` is a tree from `parse_condition`. `blank` says what a blank value is. With "value" (the default, as in
    REDCap) a blank is the empty value: it equals another blank and differs from anything else, so `[a] <> 1` is true
    when `a` is blank; only ordering a blank is unknown. With "unknown" (as in SQL) every comparison with a blank is
    unknown.
    """
    if blank not in ("value", "unknown"):
        message = f"blank must be 'value' or 'unknown', not {blank!r}"
        raise ValueError(message)
    return evaluate_node(node, row, blank == "value")


def evaluate_test(operator: str, args: list[Any], row: Row, blank_is_value: bool) -> bool | None:  # noqa: FBT001
    """The operators with one operand: IN, IS NULL and NOT."""
    if operator == "null":
        return value_of(args[0], row) is None
    if operator == "in":
        left = value_of(args[0], row)
        if left is None:
            return False if blank_is_value else None
        return any(same(left, option) for option in args[1])
    inner = evaluate_node(args[0], row, blank_is_value)
    return None if inner is None else not inner


def evaluate_node(node: Condition, row: Row, blank_is_value: bool) -> bool | None:  # noqa: FBT001
    ((operator, args),) = node.items()
    if operator in COMPARISONS:
        left, right = value_of(args[0], row), value_of(args[1], row)
        return compared(operator, left, right, blank_is_value=blank_is_value)
    if operator in ("in", "null", "!"):
        return evaluate_test(operator, args, row, blank_is_value)
    results = [evaluate_node(arg, row, blank_is_value) for arg in args]
    return all_of(results) if operator == "and" else any_of(results)
