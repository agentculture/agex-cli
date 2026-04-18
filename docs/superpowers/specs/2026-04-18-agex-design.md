# agex — agent-operated developer-experience CLI

**Date:** 2026-04-18
**Status:** Draft (pending user review)
**Scope:** v0.1 of the `agex` CLI — a non-agentic, deterministic Python CLI that emits per-backend markdown briefings and primitives that agent-authored skills wrap. Ships Claude-Code-only tester; other backends' testers are tracked as GitHub issues.

## Context

`../claude-code-guide` is a Claude Code plugin aimed at humans: an interactive guide you install into your Claude Code session. `../culture` is the opposite end — infrastructure operated by agents peer-to-peer across a mesh.

`agex` sits in between. It is the *developer experience for agents* — the things an autonomous agent needs to know and do to work well inside its own runtime (Claude Code, Codex, GitHub Copilot CLI, ACP-speaking agents like KiroCLI and OpenCode). Where `claude-code-guide` ships pre-authored skills a human invokes, `agex` ships **primitives** that agents invoke from their shell tool; any user-facing skills are authored by the agent itself, in its own native format, ensuring 100% backend fit and preserving user control over the agent's skill set.

PyPI distribution name: `agent-experience`. CLI entry point: `agex`. Both already reserved on PyPI and TestPyPI.

## Design invariants

These are load-bearing across every section of this document. If any of them changes, re-evaluate the whole design.

1. **Non-agentic.** Zero LLM calls inside agex. All output is deterministic markdown produced by Jinja templates + Python scripts. All "intelligence" (judgment, advice, prioritization) lives in agent-authored skills that consume agex's output.
2. **Markdown is the universal output format.** No `--json` flag, no structured-output mode. Markdown tables, fenced code blocks, prose. Agents already consume markdown natively.
3. **`--agent <backend>` is required** on every backend-sensitive command. No auto-detection. The CLI stays a deterministic primitive; per-backend wrappers (agent-authored skills) supply the flag.
4. **Four backends, same pattern.** Claude Code, Codex, GitHub Copilot CLI, ACP. Adding a backend is a localized change: new YAML + optional probe; no core changes.
5. **Path-aware, cwd-scoped state.** `.agex/` is created in the user's project on first use, with a committed `config.toml` and a gitignored `data/` directory.
6. **Side effects are strictly enumerated.** Only `gamify`, `gamify --uninstall`, `hook write`, and first-run `.agex/` init mutate disk. Everything else is read-only.
7. **Idempotency and reversibility for all write commands.** `gamify` is safe to call repeatedly; `gamify --uninstall` removes exactly what `gamify` wrote, preserving user-authored content.
8. **Skills are authored by the agent, not shipped by agex.** `agex learn <topic>` teaches; `agex explain <topic>` describes. agex never writes a skill file into the project on the agent's behalf (v0.1).
9. **Unsupported capabilities are first-class output.** When a backend lacks a feature, the CLI emits a markdown notice describing the gap and linking to the GitHub issue tracker for suggestions/contributions. Exit code 0 — this is a valid answer, not an error.

## Command surface (v0.1)

| Command | Purpose | Side effects |
|---|---|---|
| `agex overview --agent X` | Snapshot of the project's current setup for backend X (skills, hooks, agents, MCP, config files). Descriptive. | Read-only (plus first-run `.agex/` init). |
| `agex learn --agent X` | Menu of lesson topics available for backend X. | Read-only. |
| `agex learn <topic> --agent X` | Teach a specific lesson — renders SKILL.md with backend context + inline skill-template code blocks. | Read-only. |
| `agex gamify --agent X` | Install backend-native hooks wired to `agex hook write`. Or, if hooks unsupported on X, emit the unsupported notice. | Writes hook fragments into backend's hook file; updates `.agex/config.toml`. |
| `agex gamify --uninstall --agent X` | Remove exactly the hook fragments agex installed. Preserves user-authored content. | Reverse of `gamify`. |
| `agex hook write <event> [args...]` | Append tracking event to `.agex/data/<event>.json`. Called by installed hooks; stays silent. | Appends JSON. |
| `agex hook read --agent X` | Read tracked events across streams, render as markdown table, print source JSON path. | Read-only. |
| `agex explain <topic>` | Emit concept/command/lesson documentation as markdown. | Read-only. |

**Non-commands (deliberately out of scope for v0.1):** no `config` command (state mutated as a side effect of other commands), no top-level `levelup` (it is a lesson, not a command), no `install`/`uninstall` of agex itself (handled by `uv tool` / `pipx`).

## Architecture

Every command follows the same three-stage pipeline:

```
cli.py  ──►  command script  ──►  core renderer
                 │                       │
                 ├─► backend probe       ├─► reads SKILL.md / assets template
                 │   (reads project      │
                 │    state on disk)     ├─► injects {backend, paths, capabilities, probe_result}
                 │                       │
                 ├─► capabilities.yaml   └─► writes markdown to stdout
                 │   (supported/unsup)
                 │
                 └─► skill_loader
                     (reads SKILL.md for explain / learn)
```

### Three layers

- **`cli.py`** — argparse/Typer entry. Routes `agex <command> [args] --agent X` to the matching command script. Uniform `--agent` validation. No business logic.
- **Command scripts** (`commands/*/scripts/`) — orchestration. Each command is a skill-folder; its script pulls pieces from `core/` and its own `assets/`, emits markdown to stdout. No content lives in scripts.
- **Core plumbing** (`core/`) — shared, command-agnostic: backend registry, `.agex/` discovery, Jinja renderer, hook JSON I/O, capability matrix loader, SKILL.md loader. Command- and content-agnostic.

### Backend plug-in surface

A backend is defined by:

1. `commands/*/assets/backends/<backend>.yaml` — one YAML per command that cares about this backend.
2. `backends/<name>/probe.py` — optional Python probe for parsing that backend's on-disk state (only needed for `overview`).
3. A row in `core/backend.py`'s enum and registry.

Adding a new backend touches only those three places.

## Components

### `core/` (shared plumbing)

| Module | Responsibility |
|---|---|
| `backend.py` | `Backend` enum (`CLAUDE_CODE`, `CODEX`, `COPILOT`, `ACP`); `--agent` validation; probe registry. |
| `paths.py` | Walk up from cwd to find/init `.agex/`. Writes `.agex/.gitignore` pinning `data/` on first init. Exposes `agex_dir()`, `config_path()`, `data_dir()`. |
| `render.py` | Jinja2 environment with `StrictUndefined`. Renders a SKILL.md or `*.md.j2` against a context dict. No custom filters in v0.1. |
| `hook_io.py` | `append_event(stream, payload)` → JSON append with `fcntl.flock`. `load_events(stream)` → list. `render_table(events, columns)` → markdown table string. |
| `capabilities.py` | Loads `capabilities.yaml` per backend. `is_supported(backend, capability) -> bool`. `unsupported_notice(backend, capability) -> str`. |
| `skill_loader.py` | Parses SKILL.md frontmatter (`name`, `description`, `type`) + body. Returns a `Skill` dataclass. |
| `config.py` | Reads/writes `.agex/config.toml`. |

### `commands/` (skill-folders — one per command)

Each command is a self-contained skill-folder with four standard subdirectories. The top-level `SKILL.md` is agent-facing documentation *and* the content emitted by `agex explain <command>`.

```
commands/<command>/
  SKILL.md            # frontmatter + body; serves explain/learn/Claude-skill duty simultaneously
  scripts/            # Python implementation; invoked by cli.py
  references/         # dev-facing design notes (not emitted at runtime)
  assets/             # templates, per-backend YAML, nested sub-skills (for `learn`)
```

### `backends/` (per-backend probes)

```
backends/
  claude_code/probe.py    # reads .claude/, CLAUDE.md, ~/.claude/settings.json
  codex/probe.py          # reads AGENTS.md, ~/.codex/*
  copilot/probe.py
  acp/probe.py
```

Each implements:

```python
class BackendProbe(Protocol):
    def probe(self, project_dir: Path) -> ProbeResult: ...
```

`ProbeResult` is a dataclass with `skills: list[...], hooks: list[...], agents: list[...], mcp_servers: list[...], config_files: list[...]` — each field is optional/empty when the backend lacks that concept. Probes never raise on malformed input; they report warnings in-band and return best-effort data.

## Data flow (per command)

### `agex overview --agent claude-code`

1. `cli.py` validates `--agent`, dispatches to `commands/overview/scripts/overview.py`.
2. Load `commands/overview/assets/backends/claude-code.yaml` (section list + paths to probe).
3. Call `backends/claude_code/probe.py::probe(cwd)` → `ProbeResult`.
4. Load `commands/overview/assets/sections.md.j2`.
5. `core/render.py` renders with `{backend, paths, probe_result, capabilities}`.
6. Write rendered markdown to stdout. Exit 0.

Read-only except first-run `.agex/` init.

### `agex learn --agent claude-code` (no topic)

1. Dispatch to `learn.py`.
2. Scan `commands/learn/assets/topics/*/SKILL.md`, collect `{name, description}` frontmatter.
3. Filter by capabilities: topics gated on a backend feature (e.g., `gamify` needs hooks) are still listed but marked `[unsupported on claude-code: reason]`.
4. Render `commands/learn/assets/menu.md.j2` → stdout.

### `agex learn introspect --agent claude-code`

1. Dispatch to `learn.py introspect`.
2. Load `commands/learn/assets/topics/introspect/SKILL.md`.
3. Load template files from `commands/learn/assets/topics/introspect/assets/skill-template/claude-code/`.
4. Render SKILL.md with `{backend, template_files}`; embeds each template file as a fenced code block annotated with its target path.
5. Stdout: lesson text + inline code blocks the agent writes to disk.

### `agex gamify --agent claude-code`

1. Load `capabilities.yaml`. If hooks unsupported → emit `unsupported_notice(backend, "hooks")` to stdout, exit 0.
2. Load `commands/gamify/assets/hooks/claude-code.hooks.json`.
3. Merge into `.claude/hooks.json` (or equivalent native location). Each written fragment has a stable ID (e.g., `agex:post-tool-use`).
4. Update `.agex/config.toml`: record `installed.gamify.at` and `installed.gamify.hook_fragment_ids`.
5. Stdout: markdown confirmation + "next step: run `agex learn gamify` to set up the levelup skill."

Calling `gamify` again with the same state is a no-op; the command re-emits the success notice without rewriting files.

### `agex gamify --uninstall --agent claude-code`

1. Read `.agex/config.toml` → `installed.gamify.hook_fragment_ids`.
2. Remove exactly those fragments from the backend's hook file.
3. Delete the `[installed.gamify]` section from `config.toml`.
4. Stdout: markdown confirmation of what was removed.

### `agex hook write <event> [args]`

1. Dispatch to `hook/scripts/write.py`.
2. `core/hook_io.append_event(stream=event, payload={timestamp, agent, event, args...})`.
3. Silent (exit 0).

### `agex hook read --agent claude-code`

1. Dispatch to `read.py`.
2. `core/hook_io.load_events(stream=*)` combines all streams.
3. Render `commands/hook/assets/table.md.j2` → markdown table + `Source: .agex/data/` pointer line.
4. Stdout.

### `agex explain gamify`

Resolution order (first match wins):

1. `commands/gamify/SKILL.md` (command-level)
2. `commands/learn/assets/topics/gamify/SKILL.md` (lesson-level)
3. `commands/explain/assets/topics/gamify.md` (concept-level override)

Body rendered to stdout. Stable precedence documented inline.

### `agex explain agex`

Self-describing page — reads `commands/explain/assets/topics/agex.md`, which lists commands, points at `agex learn --agent X` for usage, and names the repo. Also emitted for unknown-command errors.

## On-disk state

### `.agex/` (in user's cwd)

```
.agex/
  .gitignore                  # pins data/ — written on init
  config.toml                 # committed
  data/                       # gitignored
    post-tool-use.json
    user-prompt.json
    stop.json
    sessions.json
```

### `config.toml` schema (v0.1)

```toml
agex_version = "0.1.0"
backend = "claude-code"         # optional convenience; CLI still requires --agent

[installed.gamify]
at = "2026-04-18T10:00:00Z"
hook_fragment_ids = ["agex:post-tool-use", "agex:user-prompt", "agex:stop"]

[preferences]
# reserved; empty in v0.1
```

`hook_fragment_ids` is the reversibility contract. `gamify --uninstall` strips exactly those IDs, nothing else.

## Error handling

### Philosophy

Agents consume markdown; stack traces are a bad UX. Every error emits markdown on stdout (useful for the agent) plus a one-line machine-readable summary on stderr (useful for shell wrappers).

### Error table

| Condition | Exit | Stdout | Stderr |
|---|---|---|---|
| Missing/invalid `--agent` | 2 | Markdown listing valid backends + why `--agent` is required | `agex: error: --agent required (one of: claude-code, codex, copilot, acp)` |
| Unknown command | 2 | Same content as `agex explain agex` (self-describing page) | `agex: error: unknown command '<foo>'` |
| Unknown `learn` topic | 2 | Topic menu (same as `agex learn --agent X` with no topic) | `agex: error: unknown topic '<foo>'` |
| Unsupported capability | 0 | Markdown explaining what's unsupported + "Want this supported? Open an issue: `https://github.com/OriNachum/agent-experience/issues`" | (none) |
| Backend probe failure on one file | 0 | Rendered output with `> ⚠️ could not parse X — skipped` inline | (none) |
| `.agex/` init failure | 1 | Markdown explaining what failed and how to recover | `agex: error: could not create .agex/ in <cwd>: <reason>` |
| Internal bug | 1 | Markdown apology + how to file an issue, with traceback fenced | `agex: internal error` |

### Design rules

1. **Probe failures never fatal.** Partial data > no data.
2. **"Unsupported" is success.** Exit 0.
3. **No retries, no sleeps, no network.** Sync, local, deterministic.
4. **Idempotency for write commands.** `gamify`, `gamify --uninstall`, and `hook write` are all safe to call repeatedly.

### Concurrency

`hook write` may run concurrently from parallel hook executions. `hook_io.append_event` uses `fcntl.flock` on POSIX; falls back to `msvcrt.locking` on Windows. No in-process state.

## Testing

### Strategy

Deterministic, file-driven CLI → snapshot tests dominate; unit tests cover core plumbing.

| Layer | Test type | Tool |
|---|---|---|
| CLI dispatch | Integration | `pytest` + Typer test runner |
| Command renders | Snapshot | `pytest` + `syrupy` — `.ambr` snapshots per `(command, backend)` |
| Backend probes | Unit | `pytest` + `tmp_path` against `tests/fixtures/<backend>/<scenario>/` |
| `hook_io` | Unit | round-trip + concurrent-append smoke test |
| `capabilities` | Unit | `is_supported` + `unsupported_notice` rendering |
| `paths` / `config` | Unit | `.agex/` init idempotency, `.gitignore` writer |
| `gamify` install/uninstall | Integration | Install → assert fragments present; uninstall → assert only agex fragments removed; idempotency |
| SKILL.md consistency | Meta-test | Frontmatter parses; required fields present; every `commands/*/SKILL.md` resolves via `explain` |

### Fixtures

```
tests/
  fixtures/
    claude-code/
      empty/
      typical/
      malformed/
    codex/...
    copilot/...
    acp/...
  __snapshots__/
```

No network, no LLM, no real hook executions.

## Repo layout

```
agent-experience/
  src/agent_experience/
    cli.py
    core/
      backend.py
      paths.py
      render.py
      hook_io.py
      capabilities.py
      skill_loader.py
      config.py
    commands/
      overview/
        SKILL.md
        scripts/overview.py
        references/
        assets/
          sections.md.j2
          backends/{claude-code,codex,copilot,acp}.yaml
      learn/
        SKILL.md
        scripts/learn.py
        references/
        assets/
          menu.md.j2
          topics/
            introspect/
              SKILL.md
              scripts/
              references/
              assets/
                skill-template/{claude-code,codex,copilot,acp}/
            visualize/   (same shape)
            gamify/      (same shape; bundles levelup sub-section)
            levelup/     (same shape; standalone entry point)
      gamify/
        SKILL.md
        scripts/install.py
        references/
        assets/hooks/{claude-code,codex,copilot,acp}.*
      hook/
        SKILL.md
        scripts/{write.py,read.py}
        references/
        assets/table.md.j2
      explain/
        SKILL.md
        scripts/explain.py
        references/
        assets/topics/{agex.md, capabilities.md, backend-detection.md, ...}
    backends/
      claude_code/probe.py
      codex/probe.py
      copilot/probe.py
      acp/probe.py
  tests/
    fixtures/
    __snapshots__/
    test_cli_*.py
    test_probe_*.py
    test_hook_io.py
    test_capabilities.py
    test_paths.py
    test_gamify.py
    test_skill_md_consistency.py
  docs/                             # Jekyll site (see below)
  tester-agents/                    # dogfooding workspaces (see below)
  .github/workflows/
    test.yml
    publish.yml
    docs.yml
    skill-md-sync.yml
  pyproject.toml                    # dist: agent-experience; script: agex
  CHANGELOG.md
  CLAUDE.md
  CONTRIBUTING.md
  LICENSE
  README.md
  .gitignore
```

## Tooling & publishing

- **Package manager:** `uv`. `uv venv && uv pip install -e ".[dev]"`.
- **Lint/format:** `black`, `isort`, `flake8`, `bandit`. Pre-commit config mirrors culture's.
- **Versioning:** single source in `pyproject.toml`; CHANGELOG.md bumped before each PR via a `/version-bump` workflow. CI version-check job enforces.
- **CI:** GitHub Actions. Matrix on Linux/macOS/Windows and Python 3.10–3.13.
- **Publishing:** TestPyPI on every merged PR; PyPI on tagged release. Both names already reserved.

## Docs site (`agent-experience.culture.dev`)

Jekyll site deployed via Cloudflare Pages. Styled to match `../culture` (cream/dark palette, `_sass/` and `_includes/` patterns lifted). Layout:

```
docs/
  _config.yml
  _sass/             # borrowed from culture
  _includes/         # borrowed from culture
  index.md           # landing
  getting-started.md
  commands/          # auto-imported from src/agent_experience/commands/*/SKILL.md
  CHANGELOG.md       # include of repo-root CHANGELOG
  Gemfile
```

Build: `bundle install && bundle exec jekyll build`. Cloudflare Pages publishes `_site/`. A `.github/workflows/docs.yml` triggers on changes to `docs/` or `src/agent_experience/commands/*/SKILL.md` (so shipping a new SKILL.md also refreshes the site).

## `tester-agents/` — dogfooding via culture

v0.1 ships **one** tester: Claude. Other backends are tracked as follow-up issues (see Open Issues).

### `tester-agents/claude/`

```
tester-agents/claude/
  CLAUDE.md                          # persona + operating instructions for the tester agent
  culture.yaml                       # identity for culture mesh (nick: <server>-agex-tester-claude)
  .claude/
    skills/                          # SYMLINK → ../../../src/agent_experience/commands/
    settings.json
  README.md                          # registration: `culture agent register tester-agents/claude/`
```

Because every `commands/<command>/` is already skill-shaped (`SKILL.md` + `scripts/` + `references/` + `assets/`), the symlink makes them appear directly as Claude Code skills — zero duplication.

### Implied constraint on every command's SKILL.md

Each command's SKILL.md serves three roles simultaneously:

1. Content emitted by `agex explain <command>`.
2. A valid Claude Code skill (frontmatter with `name`/`description`; body tells the agent when to use it and how to invoke `agex <command>` from its shell tool).
3. Reference documentation for humans.

All three satisfiable by one file if the tone is careful. Enforced by `tests/test_skill_md_consistency.py`.

### Windows limitation

Directory-level symlinks are fragile on Windows. The Windows CI matrix skips `tester-agents/claude/.claude/skills/` resolution checks. Flagged as a known issue in the README.

## Open issues (tracked on GitHub at repo creation)

The following are deliberately out of scope for v0.1 but will be filed as issues on `https://github.com/OriNachum/agent-experience/issues`:

1. **Codex tester workspace** — `tester-agents/codex/` with `AGENTS.md` persona + `culture.yaml`. Codex's native skill-discovery format (if any) to be confirmed during implementation.
2. **GitHub Copilot CLI tester workspace** — `tester-agents/copilot/` with Copilot-native instruction file + `culture.yaml`.
3. **KiroCLI tester workspace (ACP)** — `tester-agents/kiro/` with ACP-native instruction file + `culture.yaml`.
4. **OpenCode tester workspace (ACP)** — `tester-agents/opencode/` with ACP-native instruction file + `culture.yaml`. Distinct identity from `kiro/`.
5. **`agex learn <topic> --write` flag** — optional side-effect mode that writes the inline skill-template files directly into the project instead of emitting them as code blocks. v0.1 is inline-only.
6. **`agex config` command** — user-facing CLI to view/edit `.agex/config.toml` preferences. v0.1 manipulates config as a side effect of other commands only.
7. **Additional lesson topics** beyond the initial four (`introspect`, `visualize`, `gamify`, `levelup`) — e.g., `migrate`, `onboard`, `mcp-setup`.
8. **Custom Jinja filters** for SKILL.md rendering — deferred until a concrete need arises in template authoring.
