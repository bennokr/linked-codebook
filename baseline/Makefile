# One entry point for the checks. CI runs exactly `make check`; run it before every push.
.PHONY: check lint types test size

check: lint types test size

lint:
	ruff check .
	npx eslint . --max-warnings 0

types:
	mypy --strict <core modules>
	npx tsc --noEmit

test:
	pytest -q
	npm test

# Budgets only go down: scripts/check_size.py (Python) or scripts/budget.py (see linked-codebook).
size:
	python scripts/check_size.py
