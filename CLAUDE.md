# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`agex` — non-agentic Python CLI that emits deterministic per-backend markdown briefings for autonomous agents. PyPI distribution name: `agent-experience`. CLI entry point: `agex`.

**Source-of-truth documents:**

- Spec: `docs/superpowers/specs/2026-04-18-agex-design.md`
- Implementation plan: `docs/superpowers/plans/2026-04-18-agex-v0.1.md` — 33 tasks across 12 phases.
- Status: PR #1 merged Phases 1–3 (scaffolding, core, `agex explain`). Phases 4–12 (`overview`, `learn`, `gamify`, `hook`, backends, docs site, tester) remain.

Read the spec before any non-trivial change — the design invariants below are derived from it.

## Design invariants (non-negotiable)

1. **Zero LLM calls inside agex.** All output is deterministic markdown from Jinja templates + Python.
2. **Markdown is the only output format.** No `--json` flag.
3. **`--agent <backend>` is required** on backend-sensitive commands. The CLI never auto-detects.
4. **Side effects only in** `gamify`, `gamify --uninstall`, `hook write`, and first-run `.agex/` init. Everything else is read-only.
5. **"Unsupported" is success** — exit 0 with a markdown notice that links to the issue tracker, not a non-zero exit.
6. **Skills are authored by the agent, not shipped by agex.** `agex learn <topic>` teaches; `agex explain <topic>` describes; agex never writes a user skill file on the agent's behalf in v0.1.

## Architecture (3-stage pipeline)

Every command follows the same shape:

```
cli.py ──► commands/<name>/scripts/<name>.py ──► core/render.py
              │                                    │
              ├─► backends/<name>/probe.py         ├─► reads SKILL.md / *.md.j2
              │   (reads project state)            ├─► injects {backend, paths, capabilities, probe}
              └─► core/capabilities.py             └─► writes markdown to stdout
                  (supported / unsupported)
```

- `cli.py` (Typer) routes `agex <command> [args] --agent X`. No business logic.
- Each `commands/<name>/` is a **skill-folder**: `SKILL.md` + `scripts/` + `assets/` + `references/`. The `SKILL.md` doubles as the content emitted by `agex explain <command>`.
- `core/` is shared plumbing — backend enum, `.agex/` paths, Jinja renderer (`StrictUndefined`), TOML config, SKILL.md frontmatter parser, capability matrix loader, hook JSON I/O. Command- and content-agnostic.
- A backend lives in three places: `core/backend.Backend` (enum entry), `backends/<name>/probe.py` (optional Python probe), and one YAML per relevant command under `commands/*/assets/backends/<name>.yaml`. Adding a backend touches only those locations.

## Conventions worth following

- **Resource loading: use `importlib.resources.files(...)` and treat the result as a `Traversable`.** Call `.joinpath()` / `.is_file()` / `.read_text(encoding="utf-8")` directly. Wrap with `importlib.resources.as_file()` only when a third-party API needs a real `pathlib.Path`. Do NOT do `Path(str(files(...)))` — it's not zipapp/PEX safe.
- **File locking: use `portalocker.lock` / `portalocker.unlock`.** Reaching for `fcntl.flock` / `msvcrt.locking` directly is a known foot-gun on Windows (see commit `923f639`).
- **Always pass `encoding="utf-8"` to `read_text` / `write_text`.** Default locale on Windows corrupts non-ASCII output.
- **Validate user-controlled CLI args before joining into paths.** `agex explain <topic>` rejects anything that doesn't match `^[a-z][a-z0-9-]*$` to block path traversal (commit `5ac796e`, test `test_explain_rejects_path_traversal`).
- **Single source of truth for the version:** `agent_experience.__version__`. `Config.agex_version` derives from it via `field(default_factory=...)`.

## Common commands

```bash
# Bootstrap
uv venv && uv pip install -e ".[dev]"

# Full test suite (parallel; pytest-xdist via pyproject)
uv run pytest

# Single test
uv run pytest tests/core/test_paths.py::test_ensure_init_creates_dir_and_gitignore -v

# Run the CLI
uv run agex --version
uv run agex explain agex
uv run agex explain explain

# Coverage (matches what build.yml runs; SonarCloud reads this file)
uv run pytest --cov=src/agent_experience --cov-report=xml --cov-report=term
```

## CI surface

- `.github/workflows/test.yml` — matrix: 3 OS × 4 Python (3.10–3.13). Runs `uv run pytest`.
- `.github/workflows/build.yml` — single ubuntu-3.11 job that installs deps, runs `pytest --cov`, then `SonarSource/sonarqube-scan-action`. SonarCloud reads `coverage.xml` via `sonar.python.coverage.reportPaths` in `sonar-project.properties`.
- All third-party actions are **pinned to full commit SHAs** with trailing `# vN` comments (rule `githubactions:S7637`). Keep new actions pinned the same way.

## SonarCloud notes

- `python:S5496` is **narrowly suppressed** for `src/agent_experience/core/render.py` only via `sonar.issue.ignore.multicriteria` in `sonar-project.properties`. Reason: `render_string()` renders Jinja templates that are always package-shipped; output is markdown, never HTML in a browser. See the comment in `render.py` above `render_string` for the rationale. Do not widen the suppression to other files.
- The `render.py` autoescape decision is explicit (`autoescape=select_autoescape([])`). Don't change it.

## Git workflow

- Branch for all changes. Don't push to `main` directly.
- Bump version in `pyproject.toml` (and append a `[Unreleased]` line in `CHANGELOG.md`) before opening a PR.
- Push, open a PR, let CI + SonarCloud + Qodo + Copilot run. Address inline comments + resolve threads before merge.
- When posting on GitHub on the user's behalf (PR descriptions, issue replies, review-thread replies), sign with `— Claude` so it's clear the message came from an AI.
