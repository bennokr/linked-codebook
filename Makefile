.PHONY: setup generate pin golden lint test budget site smoke check

setup:
	uv sync --group dev
	npm ci

# Regenerate the schema, types, constants and generated docs from spec/*.yaml.
generate:
	uv run python scripts/generate.py

# Check the terms of the specification against the published vocabularies (needs network).
pin:
	uv run python scripts/pin_vocab.py

# Rewrite the expected outputs of the conformance cases. Review the diff.
golden:
	scripts/golden.sh

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	npx tsc -p packages/ts
	npx tsc -p site
	npx eslint packages/ts site scripts --max-warnings 0
	npx prettier --check 'packages/ts/{src,test}/**/*.ts' 'site/*.ts' 'scripts/*.ts' eslint.config.js

test:
	uv run pytest -q packages/py/tests
	cd packages/ts && node --test 'test/*.test.ts'

budget:
	uv run python scripts/budget.py

site:
	node site/build.ts

# Open the built page in a browser (needs network for Pyodide).
smoke: site
	node --test site/smoke.test.ts

check: lint test budget
