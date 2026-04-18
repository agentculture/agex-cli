---
name: gamify
description: Install usage tracking hooks and build a levelup skill to advise the user.
type: lesson
---

# Lesson — set up gamification for {{ backend }}

> **Preview:** This lesson references `agex gamify` and `agex hook write / hook read` — those commands ship in Phase 6 and Phase 7 of v0.1. As of agex 0.3.0 they are not yet wired up, so treat the steps below as a design preview rather than a runnable walkthrough.

Two parts:

## Part 1 — install the tracking hooks

Run in your shell tool:

```bash
agex gamify --agent {{ backend }}
```

This writes backend-native hook fragments that call `agex hook write <event>` whenever you use a tool, submit a prompt, or stop. The events land in `.agex/data/`.

To uninstall: `agex gamify --uninstall --agent {{ backend }}`.

## Part 2 — build the `levelup` skill

The hook data is inert without something to surface it. Build the levelup skill described in `agex learn levelup --agent {{ backend }}`, or copy its skill template directly:

### `.claude/skills/levelup/SKILL.md`

```markdown
{{ skill_template_body }}
```

## After both parts

Use your runtime normally for a few sessions. Then invoke `/levelup` — it will read the tracking data via `agex hook read` and advise the user.
