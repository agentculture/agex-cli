# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
  `malformed/`). Probe test coverage now 100%; overall project 98%.

### Changed
- Version bumped to 0.2.0 (minor — new `overview` surface, backward
  compatible).
- Renamed PyPI distribution from `agent-experience` to `agex-cli` (CLI
  entry point stays `agex`); renamed GitHub repo from
  `OriNachum/agent-experience` to `OriNachum/agex`; updated issue and
  repo URLs, Homepage (`agex.culture.dev`), and SonarCloud project key
  (`OriNachum_agex`).
