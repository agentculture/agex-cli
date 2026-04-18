# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] — 2026-04-19

### Added
- Minimal **stub probes** for the three remaining v0.1 backends:
  - `codex` — reads `AGENTS.md` into `ProbeResult.claude_md` if
    present (field name reused pending a future `project_memory`
    rename); further discovery deferred.
  - `copilot` — empty `ProbeResult()`; full discovery tracked as an
    open issue.
  - `acp` — empty `ProbeResult()`; full discovery tracked as an open
    issue.
- **Capability matrix data** under
  `src/agent_experience/backends/capabilities/` — one YAML per backend
  (`claude-code.yaml`, `codex.yaml`, `copilot.yaml`, `acp.yaml`)
  keyed by the four v0.1 capability facets (`hooks`, `mcp`, `skills`,
  `agents`) plus a `*_alternative` free-text field for unsupported
  ones. These YAMLs are loadable by the existing
  `core/capabilities.py::CapabilityMatrix.load(...)` API; callers that
  wire up capability-based routing (e.g., `learn.py`) land in a later
  phase.
- **Backend-specific overview YAMLs** for `codex`, `copilot`, `acp`
  under `commands/overview/assets/backends/` — mirror the `claude-
  code.yaml` shape so `agex overview --agent <backend>` renders a
  consistent snapshot across all four backends.

### Changed
- `commands/overview/scripts/overview.py` registers all four probes in
  `_PROBES`; the interim `if backend in _PROBES / else empty
  ProbeResult` fallback from Phase 4 is removed (every backend now has
  a probe, so the dead branch + stale "Phase 8 will..." comment are
  gone). `run(backend)` is now a direct dict lookup.

### Tests
- `tests/backends/test_stub_probes.py` — 4 new smoke tests exercising
  the three stub probes (codex empty + codex AGENTS.md + copilot
  empty + acp empty).
- `tests/commands/test_gamify.py` adds one regression test pinning
  that `agex gamify --agent codex` returns exit 0 with an
  "unsupported"-notice in stdout and does **not** create `.claude/`
  on disk (spec invariant #5: unsupported is success, no side
  effects).
- 66 tests passing (was 61 on 0.5.0).

## [0.5.0] — 2026-04-19

### Added
- `agex gamify --agent claude-code` — installs Claude Code hook
  fragments (tagged `agex:post-tool-use`, `agex:user-prompt`,
  `agex:stop`) into `.claude/hooks.json` so every tool use, prompt,
  and stop event calls `agex hook write`. Preserves user-authored
  hooks already in the file. Idempotent: re-running is a byte-
  identical no-op (the `[installed.gamify].at` timestamp is only
  rewritten when the fragment set actually changes).
- `agex gamify --uninstall --agent claude-code` — surgical removal:
  only entries whose `id` is tracked in `.agex/config.toml`'s
  `[installed.gamify].hook_fragment_ids` are stripped; user entries
  survive. Empty event arrays are deleted. The `gamify` record is
  popped from config.
- `commands/gamify/` skill-folder (`SKILL.md` doubles as
  `agex explain gamify`; `assets/hooks/claude-code.json` carries the
  three shipped fragments).
- Unsupported-backend path returns a markdown notice + issue-tracker
  link at exit 0 (spec invariant #5).
- 58 tests passing (53 from 0.4.0 + 4 plan tests + 1 corrupt-hooks-
  file guard).

### Safety
- Malformed `.claude/hooks.json` is NOT silently overwritten — the
  file is left untouched and `agex gamify` exits 2 with a clear
  stderr message pointing at the file. This is the first agex
  command with real side effects on the user's project; the error
  path was designed to make accidental data loss impossible.

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
