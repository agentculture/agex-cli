# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] — 2026-04-18

### Added
- `agex hook write <event> [key=value ...]` — append a JSON line with a
  UTC ISO timestamp + parsed `key=value` pairs to
  `.agex/data/<event>.json`. Silent, safe for concurrent invocation via
  `portalocker`. Empty keys (`=foo`) are dropped; the positional
  `<event>` always wins over any `event=...` pair.
- `agex hook read --agent <backend>` — render `.agex/data/*.json` as a
  markdown table with `ts | event | details` columns, one section per
  known stream (`post-tool-use`, `user-prompt`, `stop`, `sessions`).
  Empty streams show `_no events_`.
- `commands/hook/` skill-folder (`SKILL.md` doubles as
  `agex explain hook`; `assets/table.md.j2` for the read template).
- Typer sub-app pattern — `hook` is wired via `app.add_typer(...)` with
  two subcommands (`write` and `read`).
- 51 tests passing (46 from 0.3.0 + 3 CLI tests + 1 empty-key guard
  test + 1 malformed-JSON warning test); overall coverage 96%.

### Changed
- `core/hook_io.load_events` now catches `json.JSONDecodeError` on each
  line and emits a `warnings.warn(...)` instead of raising, keeping
  `agex hook read` read-only even when a `.agex/data/*.json` file is
  partially written or externally edited.

## [0.3.0] — 2026-04-18

### Added
- `agex learn [topic] --agent <backend>` — menu of available lessons
  without a topic, or teaches one with a topic. Lessons emit a
  Jinja-rendered markdown body plus an inline backend-native skill
  template the agent can write into the project itself. Rejects
  path-traversal topic arguments via the same `^[a-z][a-z0-9-]*$`
  whitelist as `agex explain`.
- Four v0.1 lessons under `commands/learn/assets/topics/`:
  `introspect`, `visualize`, `gamify` (bundles the `levelup` template),
  and `levelup`. Each ships with a `claude-code` skill template;
  Phase 8 will route non-claude-code backends through `capabilities.py`.
  The `gamify` and `levelup` lessons reference `agex gamify` and
  `agex hook read` which land in Phase 6/7 — both lessons carry an
  explicit "Preview" note until those commands ship.
- `commands/learn/` skill-folder (`SKILL.md` doubles as
  `agex explain learn`; `assets/menu.md.j2` for the topic menu).
- `tests/commands/test_learn.py` with 7 tests including a
  path-traversal guard mirroring the `explain` precedent. 46 tests
  passing total; overall coverage 97%.

## [0.2.0] — 2026-04-18

### Added
- `agex overview --agent claude-code` — deterministic markdown snapshot of
  a project's Claude Code setup (CLAUDE.md, skills, hooks, MCP, settings).
  Read-only except for first-run `.agex/` init. Unknown backends currently
  render as an empty snapshot; Phase 8 will route them to the
  unsupported-notice markdown.
- `backends/claude_code/probe.py` — `ProbeResult` dataclass + `probe()`
  that reuses `core/skill_loader.load_skill` for frontmatter parsing and
  records per-file warnings on malformed inputs instead of raising.
- `commands/overview/` skill-folder (`SKILL.md`, Jinja template,
  per-backend YAML). The `SKILL.md` doubles as `agex explain overview`.
- CLI `_agent_option()` helper and `@app.command("overview")` wiring.
- Test fixtures under `tests/fixtures/claude-code/` (`empty/`, `typical/`,
  `malformed/`). Probe test coverage 100%; overall project 98%.

### Changed
- Renamed PyPI distribution from `agent-experience` to `agex-cli` (CLI
  entry point stays `agex`); renamed GitHub repo from
  `OriNachum/agent-experience` to `OriNachum/agex`; updated issue and
  repo URLs, Homepage (`agex.culture.dev`), and SonarCloud project key
  (`OriNachum_agex`).
