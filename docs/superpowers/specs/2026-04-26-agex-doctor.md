# `agex doctor` — addendum

**Date:** 2026-04-26
**Status:** Draft addendum to `2026-04-18-agex-design.md`. Additive only — does not modify the v0.1 design or plan.
**Scope:** Adds a new top-level command, `agex doctor`, to the v0.1 command surface defined in the parent spec.

## Motivation

Every agent-CLI contract eventually needs a primitive for "is the install healthy and is the repo wired correctly?" — `claude doctor`, `codex doctor`, `gh auth status`. The v0.1 design (lines 31–42 of the parent spec) ships `overview`, `learn`, `gamify`, `hook`, and `explain`, but no zero-argument health check. Today the only way for an operator (agent or human) to confirm that an `agex` install is intact and the project's `.agex/` state is well-formed is to run `overview` against an arbitrary backend, which is heavier than necessary and conflates project state with backend probing.

`doctor` fills that gap. It is the smallest possible diagnostic: it answers "is anything obviously broken?" and emits a markdown checklist of things only the operator can verify by hand.

## Command surface

| Command | Purpose | Side effects |
|---|---|---|
| `agex doctor` | Run all base health checks; emit markdown report. | None. |
| `agex doctor --role <slug>` | Base checks + render an extra role-specific section. | None. |

No `--agent` flag. `doctor` is not backend-sensitive — backend probing remains the responsibility of `overview`. The deliberate omission is consistent with invariant 3 of the parent spec: `--agent` is required *only* on backend-sensitive commands.

## Inherited invariants

`doctor` is bound by every invariant in the parent spec (lines 17–28). The ones that are particularly load-bearing here:

1. **Non-agentic** — zero LLM calls; output is deterministic.
2. **Markdown is the universal output format.**
3. **Side effects are strictly enumerated** — `doctor` never writes; in particular it does **not** call `core.paths.ensure_init()`. If `.agex/` is missing, that is reported as `info` and the command continues.
4. **Unsupported is success** — there is no "unsupported on this backend" path for `doctor` (no backend), but the same philosophy applies to missing optional state: report it neutrally, exit `0`.

## Check categories (v0.1 of `doctor`)

| Category | Checks |
|---|---|
| **Install** | `agent_experience.__version__` resolves; Python ≥ 3.10; package resources reachable. |
| **Project state** | `.agex/` exists; `config.toml` parses; `.gitignore` matches `core.paths.GITIGNORE_CONTENT`; `data/` exists and is writable. |
| **Internal consistency** | Every shipped `commands/*/SKILL.md` parses with the required frontmatter; every `commands/*/assets/backends/*.yaml` loads as YAML. |
| **Operator verification** | A short markdown checklist of things `doctor` cannot verify automatically — confirming `.agex/config.toml` is committed, that the agent's shell tool can invoke `agex --version`, that `gamify` hook fragments are still in place if installed. |

The `Operator verification` category is the place where `doctor` mixes code-driven results with prose instructions for the caller (agent or human) — addressing the user requirement that the command be useful in both autonomous and human-operator contexts.

## Statuses and exit codes

| Status | Icon | Effect on exit |
|---|---|---|
| `ok`   | `✓`  | None. |
| `warn` | `⚠️` | None — exit stays `0`. |
| `info` | `·`  | None — neutral observation. |
| `fail` | `✗`  | Drives exit `1` and a one-line stderr summary. |

| Exit | Meaning |
|---|---|
| `0` | All checks `ok`, possibly with `warn` and/or `info` rows. |
| `1` | At least one `fail` row. Stderr: `agex: error: <N> health check(s) failed`. |
| `2` | CLI usage error (e.g., unknown role passed via `--role`). |

This matches the error-table conventions in the parent spec (lines 234–242).

## Role-flag extension contract

`doctor` accepts an optional `--role <slug>` flag. The slug is validated against the same regex `agex explain` already uses for topic resolution: `^[a-z][a-z0-9-]*$` — anything else exits `2` with a stderr message. (The regex is duplicated rather than imported across commands, because cross-command coupling is undesirable for what is effectively a copy-paste invariant.)

When a valid slug is passed, `doctor` looks up `commands/doctor/assets/roles/<slug>.md.j2`. If the file exists, it is rendered as an extra section after **Operator verification** and before **Summary**. If the file does not exist, `doctor` exits `2` with `agex: error: unknown role '<slug>'`.

The role asset is a Jinja template, but in this release `doctor` passes no extra context — keep role files static markdown until a use case justifies the coupling.

**This release ships zero role files.** The contract exists so role-specific diagnostics (e.g., `--role pr-review`, `--role gamify`) can be added incrementally without modifying `doctor` itself.

## Out of scope (deliberately)

The following are tracked as follow-up issues / future addenda, not part of `doctor` v0.1:

1. **Network checks** — verifying GitHub reachability, PyPI freshness, etc. `doctor` is sync, local, and offline.
2. **Backend probes** — `agex overview --agent X` already does this.
3. **Auto-fix mode** — recovery instructions are emitted as markdown for the operator to act on; `doctor` will not mutate state to "fix" what it finds.
4. **Concrete role files** — none ship in this release. The role-flag mechanism is the contract; specific roles will land as separate, smaller PRs.

## Implementation notes

- Lives at `src/agent_experience/commands/doctor/` — same skill-folder shape as the other commands (`SKILL.md`, `scripts/`, `assets/`, `references/`).
- The `SKILL.md` doubles as `agex explain doctor` content and the Claude-Code-skill body, per the implied constraint in the parent spec (lines 417–425).
- Test coverage at `tests/commands/test_doctor.py` follows the `CliRunner` convention from `test_explain.py`.
- `tests/test_skill_md_consistency.py` is updated to enumerate `doctor` alongside the other top-level commands and to bump its lower-bound discovery count.

## References

- Parent spec: `docs/superpowers/specs/2026-04-18-agex-design.md`.
- v0.1 plan (unchanged): `docs/superpowers/plans/2026-04-18-agex-v0.1.md`.
- Issue tracker: <https://github.com/agentculture/agex-cli/issues>.
