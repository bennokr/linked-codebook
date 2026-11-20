# Quality baseline

The checks that every project in this family runs, and where to copy them from. The files are in
[`baseline/`](https://github.com/bennokr/linked-codebook/tree/main/baseline); linked-codebook itself is the strictest example.

| Concern | Baseline | Where |
| --- | --- | --- |
| One entry point | `make check` = lint, types, tests, size; CI runs exactly that | `baseline/Makefile` |
| Python lint and dead code | ruff, pinned to one minor version; unused names, unused arguments, commented-out code | `baseline/ruff.toml` |
| Python types | `mypy --strict` on the cleaned modules; `ty` as an advisory job until it leaves beta | `Makefile` |
| TypeScript lint and dead code | eslint flat config with complexity, depth, function length and `--max-warnings`; tsc with `noUnusedLocals` and `noUnusedParameters` | `baseline/eslint.config.js`, `baseline/tsconfig.base.json` |
| Size and complexity | per-module statement budgets that only go down | `scripts/budget.py`, `scripts/check_size.py` in semsynth |
| Versions | one script fails when README, docs and packages disagree | `scripts/check_versions.py` |
| Dependencies | a lock file in CI (`uv sync --locked`, `npm ci`); monthly grouped Dependabot; a weekly job that installs the newest of everything | semsynth `.github/workflows/canary.yml` |
| Agent notes | `AGENTS.md` of at most 30 lines; `CLAUDE.md` containing `@AGENTS.md` | `baseline/AGENTS.template.md` |

The baseline has two tiers. New code uses the strict settings. Legacy code uses the curated settings, with today's
violations recorded as an ignore list or a warning count that may only shrink.

The baseline does not include dead-code scanners such as vulture and knip, or mutation testing. The unused-name and
unused-argument rules of ruff and the unused flags of tsc find most of what those tools would. Running vulture once by
hand on a legacy project gives a list of code to delete.

Dependabot cannot follow pins to linked-codebook, because they are URLs. The semsynth canary job compares its pin
with the latest release and warns when they differ. Other projects that depend on a release can copy that step.
