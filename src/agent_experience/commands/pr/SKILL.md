---
name: pr
description: GitHub PR lifecycle commands for agents — lint, open, read, reply, delta. Each command ends with a deterministic "Next step:" footer so the agent never has to guess what to chain.
type: command
---

# `agex pr` — PR lifecycle for agents

Five verbs, in roughly the order an agent uses them on a PR:

| Verb | Purpose |
|---|---|
| `agex pr lint` | Portability + alignment-trigger lint on the working diff. |
| `agex pr open --title T [--body-file F] [--draft] [--delayed-read]` | `gh pr create` with auto-signed body; with `--delayed-read` chains to `read --wait 180`. |
| `agex pr read [<PR>] [--wait SECS]` | Unified briefing: CI checks, SonarCloud quality gate, all comments, reviewer readiness. With `--wait`, polls until required reviewers are ready or timeout. |
| `agex pr reply <PR>` | Read JSONL replies on stdin, post each, resolve threads. |
| `agex pr delta` | Dump sibling-project `CLAUDE.md` heads + `culture.yaml` for alignment review. |

Every command ends with a `**Next step:**` footer — chase the chain without guessing.

## Side effects

Network: every command except `lint` and `delta` talks to GitHub via `gh`.
Disk: `pr open`, `pr read`, and `pr reply` append events to
`.agex/data/pr/events.jsonl`.

## Prerequisites

- `gh` (GitHub CLI) on PATH and authenticated (`gh auth login`).
- `--agent` flag, or first agent's `backend:` set in `culture.yaml`.

For each verb's full behavior, error modes, and exit codes, see
`docs/superpowers/specs/2026-05-10-agex-pr-design.md`.
