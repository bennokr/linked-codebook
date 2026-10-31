# <Project>: notes for coding agents

<One line: what it is and its shape (python API / CLI / browser app).>

## Commands
- Setup: `<uv sync --locked ... / npm ci>`
- Check (what CI runs): `<make check>`; run before every push.

## Layout
- `<dir>/`: <what lives here, three to five lines>.

## Hard rules
- Tests must not use the network; build small fixtures in `tmp_path`.
- Do not compress statements to satisfy lint or complexity limits; split functions.
- Lint debt is the `ignore` list / warning count; remove entries when fixed, never add new ones to pass.
- A new dependency goes into a named extra, not the core dependencies.
- Check at every commit whether README.md and this file need updating.

## Known debt
- <Honest list, so the next person does not rediscover it.>
