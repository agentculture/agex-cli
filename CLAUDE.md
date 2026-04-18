# CLAUDE.md

Guidance for agents working in this repository.

## Project

`agex` — non-agentic Python CLI that emits deterministic per-backend markdown briefings for autonomous agents. PyPI distribution: `agent-experience`. Spec: `docs/superpowers/specs/2026-04-18-agex-design.md`.

## Package Management

`uv` for all Python work. `uv venv && uv pip install -e ".[dev]"` to bootstrap.

## Design Invariants (non-negotiable)

1. Zero LLM calls inside agex. All output is deterministic markdown from Jinja templates.
2. `--agent <backend>` is required on backend-sensitive commands.
3. Side effects only in `gamify`, `gamify --uninstall`, `hook write`, and first-run `.agex/` init.
4. "Unsupported" is success — exit 0 with markdown notice.

## Testing

`uv run pytest` runs everything in parallel. Snapshot tests use `syrupy` — update with `--snapshot-update` only after verifying the new output manually.

## Git Workflow

- Branch for all changes.
- Bump version in `pyproject.toml` and `CHANGELOG.md` before creating a PR.
- Pre-commit hooks run `black`, `isort`, `flake8`, `bandit`.
