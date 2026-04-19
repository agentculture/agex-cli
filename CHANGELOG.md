# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.11.1] — 2026-04-19

### Fixed

- **SonarCloud quality gate — 4 open issues resolved.** After the switch
  to Automatic Analysis (`6a6160e`), project-level suppressions in
  `sonar-project.properties` stopped being honored. Re-surfaced two
  previously suppressed false positives and two real workflow-hygiene
  findings:
  - `pythonsecurity:S2083` on `commands/gamify/scripts/install.py` —
    now suppressed inline with `# NOSONAR`; backend remains enum-validated
    via `parse_backend()` before reaching the write. False positive.
  - `pythonsecurity:S5496` on `core/render.py` — now suppressed inline
    with `# NOSONAR(pythonsecurity:S5496)`; markdown-only output, Jinja
    templates are always package-shipped. False positive.
  - `githubactions:S8264` on `.github/workflows/publish.yml` — dropped
    workflow-level `permissions: contents: read` and moved it onto the
    `build` job (the only job without explicit job-level permissions).
  - `githubactions:S7630` on `.github/workflows/docs.yml` — moved
    `${{ github.head_ref }}` out of the inline `run:` script and into an
    `env:` block so a crafted PR branch name can no longer inject shell
    commands ahead of the sed sanitiser.

## [0.11.0] — 2026-04-19

### Added

- **Auto-tag + PyPI release on main.** Every push to `main` now publishes
  the stable version to TestPyPI (canary), auto-creates the `v<version>`
  git tag if missing, publishes to PyPI, and creates a GitHub Release with
  the matching CHANGELOG section. No manual tagging needed; the version
  field in `pyproject.toml` is the release signal.
- **`version-check` CI job** (`.github/workflows/test.yml`) — PRs that
  touch `src/`, `tests/`, or `pyproject.toml` without bumping the version
  fail with a sticky PR comment pointing at `/version-bump`. Mirrors the
  enforcement pattern already in use by culture.

### Changed

- Dropped the `v*` tag trigger from `publish.yml`. Manual tagging is
  superseded by the auto-tag job; tags still exist as historical/Release
  anchors, they just get created for you.

## [0.10.0] — 2026-04-19

### Added
- **`.github/workflows/publish.yml`** — automated publish pipeline.
  Every push to `main` builds an sdist + wheel and publishes to
  **TestPyPI** (`skip-existing: true` makes it idempotent across
  pushes that don't bump the version). Every push of a `v*` tag
  publishes to **PyPI**. Both jobs use **Trusted Publishing** (OIDC),
  so no API tokens are required — the matching PyPI/TestPyPI
  publishers and GitHub repo Environments (`pypi`, `testpypi`) must
  be configured once out-of-band.
- All third-party actions SHA-pinned with trailing `# vN` comments
  per project convention #10: `actions/checkout@v4`,
  `astral-sh/setup-uv@v3`, `actions/setup-python@v5`,
  `actions/upload-artifact@v4`, `actions/download-artifact@v4`,
  `pypa/gh-action-pypi-publish@release/v1`.

### Release notes
This is the closing phase of the v0.1 implementation plan. Phases
1–11 + 13 shipped the CLI, docs site (with per-PR previews), the
Claude dogfooding workspace, and the docs-drift guards. Phase 12
(this release) lights up the publishing pipeline — `agex-cli` is
now installable from TestPyPI via `uv tool install --index-url
https://test.pypi.org/simple/ agex-cli` immediately after the first
post-merge build, and from PyPI after the maintainer pushes a
`v0.10.0` tag.

## [0.9.0] — 2026-04-19

### Added
- **`tester-agents/claude/`** — culture-meshed dogfooding workspace
  that exercises every `agex` command end-to-end from a Claude Code
  runtime. Ships `CLAUDE.md` (persona + ordered test plan),
  `culture.yaml` (mesh config), `.claude/settings.json` (allows
  `Bash(agex:*)`), and a `README.md` with registration instructions.
- **Symlink** `tester-agents/claude/.claude/skills →
  ../../../src/agent_experience/commands` so the tester invokes the
  same `SKILL.md` files the CLI ships — no stale-copy drift. Git
  stores mode `120000`; on Windows clones, directory symlinks need
  Developer Mode or an elevated shell with `core.symlinks=true` (per
  the spec's known platform limitation, documented in the workspace
  README).

## [0.8.0] — 2026-04-19

### Added
- **Jekyll documentation site** under `docs/` — landing page
  (`index.md`), `getting-started.md`, and auto-imported `commands/`
  pages (one per top-level command, plus a `Commands` parent index).
  Styled with the same just-the-docs `dark-terminal` theme + `_sass`
  overlay used by culture / agentic-human / agentic-guides so the
  agentic sites share a visual identity. Builds cleanly via
  `bundle exec jekyll build`.
- **`scripts/sync_skill_md.py`** — reuses the in-repo
  `skill_loader.load_skill` to strip each command's agex-flavored YAML
  frontmatter and emit a Jekyll-friendly one (`title`, `layout`,
  `parent`, `nav_order`). Iterates `src/agent_experience/commands/` in
  sorted order; writes with `encoding="utf-8"`. Lessons
  (`learn/assets/topics/*`) stay in CLI territory for v0.1.
- **`.github/workflows/docs.yml`** — triggers on `docs/**`,
  `commands/**/SKILL.md`, `skill_loader.py`, the sync script, and the
  workflow itself. Runs `sync_skill_md.py` before building so the
  deployed site cannot drift from the CLI's shipped docs. Deploys to
  Cloudflare Pages (project `agex`) on push-to-main only — PRs never
  deploy.

### Changed
- Swapped the plan's reference from `cloudflare/pages-action@v1` (now
  archived / DEPRECATED upstream) to `cloudflare/wrangler-action@v3`
  with `pages deploy`. All third-party actions SHA-pinned with
  trailing `# vN` comments per project convention.

### Notes
- The Cloudflare Pages project (`agex`) and the `agex.culture.dev`
  custom-domain binding require a one-time manual setup step in the
  Cloudflare dashboard; the workflow expects `CLOUDFLARE_API_TOKEN`
  and `CLOUDFLARE_ACCOUNT_ID` repo secrets. Tracked separately.

## [0.7.0] — 2026-04-19

### Added
- **Unknown-command routing** — invoking `agex <unknown>` (e.g.,
  `agex frobnicate`) now prints a one-line
  `agex: error: unknown command '<name>'` to stderr, emits the body of
  `agex explain agex` to stdout (so the agent immediately sees the full
  command list), and exits with code 2. Previously Typer's default
  "No such command" message was emitted with no recovery guidance.
  Implemented via a thin `_main_entrypoint` wrapper in `cli.py` and a
  new `agent_experience/__main__.py` so `python -m agent_experience`
  routes through the same handler as the `agex` console script.
- **SKILL.md consistency meta-test** — `tests/test_skill_md_consistency.py`
  parametrizes over every `SKILL.md` shipped under the `commands/`
  package and asserts valid frontmatter (`name`, `description`,
  `type ∈ {command, lesson}`). A companion guard test
  (`test_meta_test_discovers_all_known_skills`) fails loudly if the
  resource-discovery glob returns fewer than the expected 9 files, so
  a future packaging regression cannot silently turn every parametrize
  case into a zero-item pass-through. 15 new tests total.

### Changed
- `pyproject.toml` script entry flipped from
  `agent_experience.cli:app` to `agent_experience.cli:_main_entrypoint`
  so the unknown-command router runs before Typer's dispatcher.

### Fixed
- **#12** — `agex hook write` on Windows + Python 3.13 occasionally
  aborted with `portalocker.exceptions.AlreadyLocked` when two
  concurrent writers raced for the append lock (the kernel surfaces
  `EDEADLK` from `msvcrt.locking()`; portalocker maps it to
  `AlreadyLocked`). `core/hook_io.append_event` now retries up to
  `_LOCK_MAX_ATTEMPTS = 5` times with jittered linear backoff
  (`10ms × attempt + up to 10ms of jitter`), re-raising only if every
  attempt fails. Two deterministic regression tests monkeypatch
  `portalocker.lock` to simulate the flake and verify both the
  recovery and the final-giveup paths.

## [0.6.0] — 2026-04-19

### Added
- Minimal **stub probes** for the three remaining v0.1 backends:
  - `codex` — records the `AGENTS.md` path in
    `ProbeResult.claude_md` if present (field name reused pending a
    future `project_memory` rename); the probe does not read the
    file's contents. Further discovery deferred.
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
